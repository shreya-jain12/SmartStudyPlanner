import streamlit as st
import subprocess
import os
import graphviz
from datetime import datetime, timedelta

ADMIN_ID = "admin"
ADMIN_PASS = "admin123"

def user_exists(userid):
    if not os.path.exists("users.txt"):
        return False
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2 and parts[1] == userid:
                return True
    return False

def get_userid_login(userid, password):
    if userid == ADMIN_ID and password == ADMIN_PASS:
        return "Admin"
    if not os.path.exists("users.txt"):
        return None
    with open("users.txt", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 3 and parts[1] == userid and parts[2] == password:
                return parts[0]  # return name
    return None

def register_user(name, userid, password):
    with open("users.txt", "a", encoding="utf-8") as f:
        f.write(f"{name},{userid},{password}\n")

def get_user_plan_file(userid):
    return f"plans_{userid}.txt"

def load_topics(filename="topics1.txt"):
    topics = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if parts and parts[0]:
                    topics.append(parts[0])
    except Exception as e:
        pass
    return topics

def parse_study_plan(filename="output.txt"):
    order = []
    times = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- "):
                parts = line[2:].split("(Estimated time:")
                topic = parts[0].strip()
                time = int(parts[1].replace("hours)", "").strip()) if len(parts) > 1 else 1
                order.append(topic)
                times.append(time)
    return order, times

def generate_flowchart(order):
    dot = graphviz.Digraph(comment='Study Plan Flow')
    for idx, topic in enumerate(order):
        dot.node(str(idx), topic)
        if idx > 0:
            dot.edge(str(idx-1), str(idx))
    return dot

def generate_timetable(order, times, start_time_str="09:00"):
    timetable = []
    current_time = datetime.strptime(start_time_str, "%H:%M")
    for topic, hours in zip(order, times):
        end_time = current_time + timedelta(hours=hours)
        timetable.append(f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}: {topic} ({hours} hours)")
        current_time = end_time
    return "\n".join(timetable)

st.title("📚 Smart Study Planner")
menu = st.sidebar.selectbox("Choose", ["Login", "Register"])

if menu == "Register":
    st.header("📝 Register New User")
    name = st.text_input("Full Name")
    userid = st.text_input("Choose a Unique User ID")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if not name.strip() or not userid.strip() or not password.strip():
            st.warning("Please fill all fields.")
        elif user_exists(userid):
            st.error("This User ID is already taken. Please choose another.")
        else:
            register_user(name.strip(), userid.strip(), password.strip())
            st.success("Registration successful! You can now login.")

elif menu == "Login":
    st.header("🔐 Login")
    userid = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        name = get_userid_login(userid.strip(), password.strip())
        if name:
            st.success(f"Welcome, {name} (User ID: {userid})!")
            st.session_state['userid'] = userid
            st.session_state['name'] = name
        else:
            st.error("Invalid User ID or Password.")

# --- Study Planner UI (only after login) ---
userid = st.session_state.get('userid')
name = st.session_state.get('name')

if userid and name:
    # --- Admin: Only Add Topic ---
    if userid == ADMIN_ID:
        st.markdown("---")
        st.header("➕ Add a New Topic (Admin Only)")
        all_topics = load_topics()
        new_topic = st.text_input("Topic Name")
        new_prereq = st.text_input("Prerequisites (separate multiple by semicolon ; )")
        new_time = st.text_input("Estimated Time (in hours, e.g. 4)")

        # --- Prerequisite Suggestions ---
        if new_prereq.strip():
            last_part = new_prereq.split(";")[-1].strip()
            if last_part:
                suggestions = [t for t in all_topics if last_part.lower() in t.lower()]
                if suggestions:
                    st.markdown("**Prerequisite Suggestions:**")
                    for s in suggestions[:10]:
                        st.write(f"- {s}")

        if st.button("Add Topic"):
            if not new_topic.strip() or not new_time.strip():
                st.warning("Please enter both topic name and estimated time.")
            else:
                topic = new_topic.strip()
                prereq = new_prereq.strip()
                time = new_time.strip()
                if prereq.lower() == "none":
                    prereq = ""
                try:
                    with open("topics1.txt", "a", encoding="utf-8") as f:
                        f.write(f"{topic},{prereq},{time}\n")
                    st.success(f"✅ Topic '{topic}' added successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to add topic: {e}")
    # --- Normal User: Study Planner ---
    else:
        st.markdown("---")
        st.header("Generate Your Study Plan")
        all_topics = load_topics()
        user_input = st.text_input("Enter your subject and get your study plan:")

        # --- Show search suggestions ---
        if user_input.strip():
            suggestions = [t for t in all_topics if user_input.lower() in t.lower()]
            if suggestions:
                st.markdown("**Suggestions:**")
                for s in suggestions[:10]:
                    st.write(f"- {s}")

        # --- Generate Plan Button ---
        current_plan = ""
        if st.button("Generate Plan"):
            with open("input.txt", "w") as file:
                file.write(user_input.strip())
            try:
                subprocess.run(["study_planner.exe"], check=True)
                st.success("✅ Study plan generated successfully.")
                # Read output from file
                with open("output.txt", "r") as file:
                    output_contents = file.read().strip()
                    if output_contents:
                        st.subheader("📖 Your Study Plan:")
                        st.text(output_contents)
                        # Save plan to user file (history)
                        plan_file = get_user_plan_file(userid)
                        with open(plan_file, "a", encoding="utf-8") as f:
                            f.write(f"---\n{user_input}\n{output_contents}\n")
                        # Prepare current plan for download
                        current_plan = f"User Name: {name}\nUser ID: {userid}\n\nSubject: {user_input}\n\n{output_contents}"
                        st.download_button(
                            "Download This Study Plan",
                            current_plan,
                            file_name=f"{userid}_{user_input.replace(' ','_')}_plan.txt"
                        )
                        # --- Flowchart & Timetable Features ---
                        order, times = parse_study_plan("output.txt")
                        if order and times:
                            # Flowchart
                            dot = generate_flowchart(order)
                            dot.render('study_plan_flowchart', format='png')
                            st.image('study_plan_flowchart.png', caption="Study Plan Flowchart")
                            with open('study_plan_flowchart.png', 'rb') as img_file:
                                st.download_button(
                                    "Download Flowchart",
                                    img_file.read(),
                                    file_name="study_plan_flowchart.png"
                                )
                            # Timetable: User se start time lo
                            start_time_str = st.text_input(
                                "Enter your study start time (HH:MM, e.g. 09:00)", value="09:00"
                            )
                            timetable = generate_timetable(order, times, start_time_str)
                            st.subheader("🕒 Real-Time Timetable")
                            st.text(timetable)
                            st.download_button("Download Timetable", timetable, file_name="timetable.txt")
                        else:
                            st.info("Flowchart/timetable banane ke liye output.txt me topics aur time sahi format me hone chahiye.")
                    else:
                        st.warning("⚠️ No relevant study plan found for the entered subject.")
            except Exception as e:
                st.error(f"❌ Failed to run the study planner or read output.\n{e}")

        # --- Previous Study Plans List & Download ---
        plan_file = get_user_plan_file(userid)
        if os.path.exists(plan_file):
            with open(plan_file, "r", encoding="utf-8") as f:
                plans_raw = f.read()
            # Split plans by "---"
            plans = [p.strip() for p in plans_raw.split("---") if p.strip()]
            st.subheader("📚 Your Previous Study Plans")
            for idx, plan in enumerate(plans, 1):
                # First line: subject, then plan
                lines = plan.split('\n', 1)
                subject = lines[0] if lines else f"Plan {idx}"
                plan_content = lines[1] if len(lines) > 1 else ""
                download_content = f"User Name: {name}\nUser ID: {userid}\n\nSubject: {subject}\n\n{plan_content}"
                with st.expander(f"{idx}. {subject}"):
                    st.text(plan_content)
                    st.download_button(
                        f"Download Plan {idx}",
                        download_content,
                        file_name=f"{userid}_{subject.replace(' ','_')}_plan.txt"
                    )
        else:
            st.info("No study plans found yet.")
else:
    st.info("Please login to use the study planner.")