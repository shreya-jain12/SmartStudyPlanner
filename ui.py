import streamlit as st
import subprocess
import os
from pathlib import Path

# session states
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.set_page_config(page_title="Smart Study Planner", layout="centered")

# Home Page function
def home_page():
    st.markdown("<h1 style='text-align: center;'>Welcome To Study Planner</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Choose an option to continue:</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col2:
        if st.button("🔐Login"):
            st.session_state.page = "login"
            st.rerun()
    with col5:
        if st.button("📝Register"):
            st.session_state.page = "register"
            st.rerun()

# Login Page function
def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        try:
            with open("users.txt", "r") as file:
                users = {line.split(",")[0].strip(): line.split(",")[1].strip() for line in file if "," in line}
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "planner"
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        except FileNotFoundError:
            st.error("User database not found. Please register first.")

# Register Page
def register_page():
    st.title("📝 Register")
    username = st.text_input("Choose a Username", key="register_user")
    password = st.text_input("Choose a Password", type="password", key="register_pass")
    if st.button("Register"):
        if username and password:
            try:
                existing_users = set()
                try:
                    with open("users.txt", "r") as file:
                        existing_users = {line.strip().split(",")[0] for line in file if "," in line}
                except FileNotFoundError:
                    st.warning("No Database found")
                if username in existing_users:
                    st.error("Username already exists, please choose another")
                else:
                    with open("users.txt", "a") as file:
                        file.write(f"{username},{password}\n")
                    st.success("Registration successful")
                    st.session_state.page = "login"
                    st.rerun()
            except Exception as e:
                st.error(f"Registration failed: {str(e)}")
        else:
            st.error("Please fill in both fields")

# Planner Page
def planner_page():
    st.title(" Smart Study Planner")
    if st.session_state.logged_in:
        st.success(f"Welcome, {st.session_state.username} Buddy, Let's Create Your Study Plan Together!")

    try:
        with open("topics1.txt", "r") as f:
            all_lines = [line.strip() for line in f if line.strip()]
            all_topics = [line.split(",")[0] for line in all_lines if "," in line]
    except FileNotFoundError:
        st.error("Topics file not found.")
        return

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    st.session_state.user_input = st.text_input("Enter a Topic and get your study plan:", st.session_state.user_input)

    if st.session_state.user_input.strip():
        suggestions = [t for t in all_topics if st.session_state.user_input.lower() in t.lower()]
        if suggestions:
            st.markdown("**Suggestions:**")
            for s in suggestions[:10]:
                st.write(f"- {s}")
        else:
            st.warning("No suggestions found.")

    col1, _, _, col5, col6, col7 = st.columns([2, 2, 1, 1, 1, 1])
    with col1:
        generate_clicked = st.button("Generate Plan")
    with col7:
        myplan_clicked = st.button("My Plan")

    if generate_clicked and st.session_state.user_input.strip():
        with open("input.txt", "w") as file:
            file.write(st.session_state.user_input.strip())
        try:
            subprocess.run(["study_planner.exe"], check=True)
            st.success("✅ Study plan generated.")

            with open("output.txt", "r") as file:
                lines = file.readlines()

            lines_before_empty = []
            lines_after_first = []
            lines_after_second = []

            count = 0
            collecting = False
            for i, line in enumerate(lines):
                if line.strip() == "":
                    count += 1
                    if count == 1:
                        if i + 1 < len(lines):
                            lines_after_first.append(lines[i + 1].strip())
                    elif count == 2:
                        collecting = True
                    continue
                if count < 1:
                    lines_before_empty.append(line.strip())
                elif collecting:
                    lines_after_second.append(line.strip())

            st.markdown("<h3 style='text-align: center;'>📖 Your Study Plan:</h3>", unsafe_allow_html=True)
            st.success("Note: Start from Bottom to Top")
            st.code("\n".join(lines_before_empty))
            if lines_after_first:
                st.success(f"{lines_after_first[0]}")
            st.markdown("<p style='color:blue; text-align: center; font-size: 22px;'>Suggested Topics to Study:</p>", unsafe_allow_html=True)
            if lines_after_second:
                st.code("\n".join(lines_after_second), language="text")
#save the plan path just after generating the plan
            downloads_path = str(Path.home() / "Downloads")
            filename = f"{st.session_state.username}.txt"
            file_path = os.path.join(downloads_path, filename)
            with open(file_path, "w") as f:
                f.write("\n".join(lines_before_empty) + "\n\n" + "\n".join(lines_after_second))
            with open("user_files.txt", "a") as f:
                f.write(f"{st.session_state.username},{file_path}\n")

            st.download_button("Download Plan", "\n".join(lines_before_empty) + "\n\n" + "\n".join(lines_after_second), filename)
        except Exception as e:
            st.error(f"Failed to generate or display the plan: {e}")

    if myplan_clicked:
        st.session_state.page = "last_saved_plan"
        st.rerun()

    col1, _, _, col5, col6, col7 = st.columns([2, 2, 1, 1, 1, 1])
    with col7:
        if st.button("Logout"):
            output_file = "output.txt"
            if os.path.exists(output_file):
                with open(output_file, "w") as f:
                    f.write("") 
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "home"
            st.rerun()
    with col1:
        show_flowchart = st.button("Show Flowchart", key="show_flowchart_button")

    def create_flowchart():
        st.success("Flowchart is ready")
        with st.expander("Flowchart Output", expanded=True):
            try:
                with open("output.txt", "r") as f:
                    lines = f.readlines()
                    for index, line in enumerate(lines):
                        if line.strip():
                            formatted_line = f"""
                            <div style="border: 3px solid #00AFFF; padding: 25px; 
                                        border-radius: 12px; background-color: #071330; 
                                        text-align: center; margin-bottom: 18px;">
                                <span style="font-size: 22px; font-weight: bold; color: #FFFFFF;">{line.strip()}</span>
                            </div>
                            """
                            st.markdown(formatted_line, unsafe_allow_html=True)
                            if index + 1 < len(lines) and lines[index + 1].strip():
                                st.markdown("<h3 style='text-align: center; font-size: 40px; color: #00AFFF;'>⬇</h3>", unsafe_allow_html=True)
                        else:
                            break
            except FileNotFoundError:
                st.error("The file 'output.txt' was not found.")

    if st.session_state.logged_in and show_flowchart:
        create_flowchart()

# Last Saved Plan
def last_saved_plan():
    username = st.session_state.get("username", None)
    if not username:
        st.error("User not logged in.")
        return

    found_plan = False
    try:
        with open("user_files.txt", "r") as user_file:
            for line in user_file:
                if line.startswith(username + ","):
                    last_plan_path = line.strip().split(",")[1]

                    if os.path.exists(last_plan_path):
                        found_plan = True
                        st.subheader("📄 Your Last Saved Plan:")

                        with open(last_plan_path, "r") as plan_file:
                            lines = plan_file.readlines()

                        before_first_blank = []
                        after_first_blank_line = []
                        after_second_blank_lines = []

                        blank_line_count = 0
                        collecting_after_second_blank = False

                        for i, line in enumerate(lines):
                            stripped_line = line.strip()
                            if stripped_line == "":
                                blank_line_count += 1
                                if blank_line_count == 1 and i + 1 < len(lines):
                                    after_first_blank_line.append(lines[i + 1].strip())
                                elif blank_line_count == 2:
                                    collecting_after_second_blank = True
                                continue

                            if blank_line_count == 0:
                                before_first_blank.append(stripped_line)
                            elif collecting_after_second_blank:
                                after_second_blank_lines.append(stripped_line)

                        st.code("\n".join(before_first_blank))
                        if after_first_blank_line:
                            st.success(after_first_blank_line[0])
                        if after_second_blank_lines:
                            st.markdown("**Suggested Topics to Study:**")
                            st.code("\n".join(after_second_blank_lines))

                    break

        if not found_plan:
            st.warning("No saved plan found for your user.")

    except FileNotFoundError:
        st.warning("User plan record file 'user_files.txt' not found.")

    #  Back to Planner button 
    if st.button("⬅️ Go Back to Planner"):
        st.session_state.page = "planner"
        st.rerun()

    
# Main router logic
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "register":
    register_page()
elif st.session_state.page == "planner":
    planner_page()
elif st.session_state.page == "last_saved_plan":
    last_saved_plan()
