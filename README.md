# 🏥 Healthcare Support Triage (AI Agent)

An AI-powered support triage system that classifies incoming messages, generates tickets, and suggests resolutions automatically.

## 🚀 What it does

This app takes a support message and:

1. **Classifies** it as:
   - Ticket (real issue)
   - Spam

2. **Creates a ticket** with:
   - ID
   - Title
   - Urgency
   - Severity score for ranking

3. **Generates resolution guidance**:
   - Root cause analysis
   - Recommended next steps
   - Suggested customer response

4. **Maintains a session queue**:
   - Keeps all triaged tickets in the current session
   - Starts with a fresh ticket queue every new session (demo mode)
   - Ranks tickets from most important to least important
   - Lets you re-enter a previously triaged ticket into the input box

## 🧠 Tech Stack

- Python
- Streamlit (UI)
- OpenAI Agents SDK
- Structured JSON outputs
- Workflow-based AI reasoning

## 🖥️ Demo

Paste a support message like:

> "We can’t submit prior authorizations, system is down"

→ The app will:
- classify it
- generate a ticket
- suggest next steps + response

## ⚙️ How to run locally

```bash
pip install -r requirements.txt
streamlit run ticket_app.py
```
