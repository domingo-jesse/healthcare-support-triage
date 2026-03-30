\# 🏥 Healthcare Support Triage (AI Agent)



An AI-powered support triage system that classifies incoming messages, generates tickets, and suggests resolutions automatically.



\## 🚀 What it does



This app takes a support message and:



1\. \*\*Classifies\*\* it as:

&#x20;  - Ticket (real issue)

&#x20;  - Spam



2\. \*\*Creates a ticket\*\* with:

&#x20;  - ID

&#x20;  - Title

&#x20;  - Urgency



3\. \*\*Generates resolution guidance\*\*:

&#x20;  - Root cause analysis

&#x20;  - Recommended next steps

&#x20;  - Suggested customer response



\## 🧠 Tech Stack



\- Python

\- Streamlit (UI)

\- OpenAI Agents SDK

\- Structured JSON outputs

\- Workflow-based AI reasoning



\## 🖥️ Demo



Paste a support message like:



> “We can’t submit prior authorizations, system is down”



→ The app will:

\- classify it

\- generate a ticket

\- suggest next steps + response



\## ⚙️ How to run locally



```bash

pip install -r requirements.txt

streamlit run ticket\_app.py

