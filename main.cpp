#include <iostream>
#include <unordered_map>
#include <vector>
#include <string>
#include <fstream>
#include <algorithm>
#include <set>
#include <sstream>
using namespace std;

struct Topic {
    string name;
    vector<string> prerequisites;
    int timeMinutes;
};

unordered_map<string, Topic> topics;
unordered_map<string, bool> visited;
unordered_map<string, bool> onStack;
vector<string> order;

unordered_map<string, vector<string>> reverseDeps;

string toLower(const string& s) {
    string res = s;
    transform(res.begin(), res.end(), res.begin(), ::tolower);
    return res;
}

string trim(const string& s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    size_t end = s.find_last_not_of(" \t\r\n");
    if (start == string::npos || end == string::npos) return "";
    return s.substr(start, end - start + 1);
}

bool dfs(const string& topic) {
    if (onStack[topic]) return false;
    if (visited[topic]) return true;

    visited[topic] = true;
    onStack[topic] = true;

    for (const string& pre : topics[topic].prerequisites) {
        if (!pre.empty() && topics.count(pre)) {
            if (!dfs(pre)) return false;
        }
    }

    onStack[topic] = false;
    order.push_back(topic);
    return true;
}

bool topologicalSort(const string& start_topic) {
    order.clear();
    visited.clear();
    onStack.clear();
    return dfs(start_topic);
}

int main() {
    ifstream file("topics1.txt");
    if (!file.is_open()) {
        cerr << "Failed to open topics.txt\n";
        return 1;
    }

    string line;
    while (getline(file, line)) {
        // Split line into 3 parts: name, prereqStr, timeStr
        stringstream ss(line);
        string name, prereqStr, timeStr;
        getline(ss, name, ',');
        getline(ss, prereqStr, ',');
        getline(ss, timeStr, ',');

        name = trim(name);
        prereqStr = trim(prereqStr);
        timeStr = trim(timeStr);

        vector<string> prereqs;
        if (!prereqStr.empty() && prereqStr != "None") {
            stringstream pss(prereqStr);
            string pre;
            while (getline(pss, pre, ';')) {
                pre = trim(toLower(pre));
                if (!pre.empty())
                    prereqs.push_back(pre);
            }
        }

        int timeMins = 0;
        try {
            timeMins = stoi(timeStr);
        } catch (...) {
            timeMins = 0;
        }
        string nameLower = toLower(name);
        topics[nameLower] = {nameLower, prereqs, timeMins};
    }
    file.close();

    // Build reverse dependency map
    for (auto it = topics.begin(); it != topics.end(); ++it) {
        const string& topicName = it->first;
        const Topic& topicData = it->second;
        for (const string& pre : topicData.prerequisites) {
            reverseDeps[pre].push_back(topicName);
        }
    }

    ifstream inputFile("input.txt");
    if (!inputFile.is_open()) {
        cerr << "Failed to open input.txt\n";
        return 1;
    }

    string input_topic;
    getline(inputFile, input_topic);
    inputFile.close();

    string topic_key = toLower(trim(input_topic));

    ofstream outputFile("output.txt");
    if (!outputFile.is_open()) {
        cerr << "Failed to write to output.txt\n";
        return 1;
    }

    if (topics.find(topic_key) == topics.end()) {
        outputFile << "Topic not found in dataset.\n";
        return 0;
    }

    if (!topologicalSort(topic_key)) {
        outputFile << "Cannot generate study plan due to cycle in prerequisites.\n";
        return 1;
    }

    outputFile << "Study Plan (start from bottom prerequisites):\n";

    int totalTime = 0;
    for (auto it = order.rbegin(); it != order.rend(); ++it) {
        string t = *it;
        string t_cap = t;
        if (!t_cap.empty()) t_cap[0] = toupper(t_cap[0]);
        int tTime = 0;
        if (topics.find(t) != topics.end())
            tTime = topics[t].timeMinutes;
        totalTime += tTime;
        outputFile << "- " << t_cap << " (Estimated time: " << tTime << " hours)\n";
    }

    outputFile << "\nTotal Estimated Time: " << totalTime << " hours\n\n";

    outputFile << "Further Suggested Topics (that depend on '" << input_topic << "'):\n";
    set<string> suggested;

    for (const string& dep : reverseDeps[topic_key]) {
        string t = dep;
        if (!t.empty()) t[0] = toupper(t[0]);
        suggested.insert(t);
    }

    if (suggested.empty()) {
        outputFile << "No further suggested topics found.\n";
    } else {
        for (const string& s : suggested) {
            outputFile << "- " << s << "\n";
        }
    }

    outputFile.close();
    cout << "Study plan with time estimation generated in output.txt\n";
   return 0;
}