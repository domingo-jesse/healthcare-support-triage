import asyncio
import csv
import html
import io
import random
import re
from datetime import datetime, timedelta, timezone

import streamlit as st

from workflow_backend import WorkflowInput, run_workflow

st.set_page_config(
    page_title="Healthcare Support Triage",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        :root {
            --bg-primary: #f6f8fb;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f8fafc;
            --text-primary: #1f2937;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
            --accent: #3b82f6;
            --accent-soft: #eff6ff;
        }
        .main, .stApp {
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        [data-testid="stHeader"] {
            background: transparent;
            border-bottom: 0;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            max-width: 100%;
            width: 100%;
            margin: 0;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        section[data-testid="stSidebar"] {
            min-width: clamp(260px, 22vw, 360px) !important;
            max-width: clamp(260px, 22vw, 360px) !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 100% !important;
        }
        .three-col-header {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }
        .hero-shell {
            position: relative;
            text-align: left;
            margin-bottom: 1.2rem;
            padding: 1.2rem 1.1rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: linear-gradient(125deg, rgba(255,255,255,0.94), rgba(239,246,255,0.8));
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
            overflow: hidden;
            isolation: isolate;
        }
        .hero-shell::before {
            content: "";
            position: absolute;
            inset: -50% auto auto -30%;
            width: 300px;
            height: 300px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(59,130,246,0.2), rgba(59,130,246,0));
            animation: floatGlow 8s ease-in-out infinite;
            pointer-events: none;
            z-index: -1;
        }
        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -20% -70% auto;
            width: 260px;
            height: 260px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(129,140,248,0.22), rgba(129,140,248,0));
            animation: floatGlow 10s ease-in-out infinite reverse;
            pointer-events: none;
            z-index: -1;
        }
        .app-title {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            flex-wrap: wrap;
            gap: 0.55rem;
            font-size: clamp(1.7rem, 3vw, 2.2rem);
            font-weight: 800;
            margin-bottom: 0.25rem;
            color: #0f172a;
            letter-spacing: -0.02em;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }
        .app-subtitle {
            color: #475569;
            margin: 0 0 0.9rem;
            max-width: min(100%, 860px);
            font-size: 0.97rem;
        }
        .hero-metrics {
            display: flex;
            gap: 0.55rem;
            flex-wrap: wrap;
            justify-content: flex-start;
        }
        .hero-pill {
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(148,163,184,0.25);
            color: #1e293b;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.28rem 0.7rem;
            animation: pulsePill 3s ease-in-out infinite;
        }
        .hero-pill:nth-child(2) { animation-delay: 0.4s; }
        .hero-pill:nth-child(3) { animation-delay: 0.8s; }
        .panel-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(226, 232, 240, 0.95);
            border-radius: 14px;
            padding: 1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
            backdrop-filter: blur(4px);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }
        .panel-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.09);
        }
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 0.7rem;
        }
        .metric-label {
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-bottom: 0.2rem;
        }
        .metric-value {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 700;
        }
        .badge-low, .badge-medium, .badge-high, .badge-spam {
            background: #eef2f7;
            color: #334155;
        }
        .ticket-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-top: 0.2rem;
            margin-bottom: 0.35rem;
        }
        .section-label {
            font-size: 0.76rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-top: 0.2rem;
            margin-bottom: 0.25rem;
        }
        .response-box {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.65rem 0.75rem;
            white-space: pre-wrap;
            line-height: 1.45;
            color: var(--text-primary);
        }
        .section-spacer {
            display: none;
            height: 0;
        }
        .analytics-shell {
            background: linear-gradient(145deg, rgba(248,250,252,0.92), rgba(241,245,249,0.78));
            border: 1px solid rgba(203, 213, 225, 0.8);
            border-radius: 16px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.3rem;
        }
        .analytics-kpi {
            background: transparent;
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 12px;
            padding: 0.65rem 0.7rem;
        }
        .analytics-kpi-label {
            font-size: 0.74rem;
            color: #64748b;
            margin-bottom: 0.2rem;
        }
        .analytics-kpi-value {
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.05;
            color: #0f172a;
        }
        .analytics-kpi-note {
            font-size: 0.72rem;
            color: #475569;
            margin-top: 0.2rem;
        }
        .analytics-subgrid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.55rem;
        }
        .analytics-chip {
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 12px;
            padding: 0.55rem 0.65rem;
            background: rgba(248, 250, 252, 0.45);
        }
        .analytics-chip-label {
            font-size: 0.72rem;
            color: #64748b;
        }
        .analytics-chip-value {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 0.1rem;
        }
        .analytics-recent-list {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
            margin-top: 0.55rem;
        }
        .analytics-chart-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.75rem;
        }
        .analytics-chart-card {
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 12px;
            padding: 0.75rem;
            background: rgba(255, 255, 255, 0.75);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
        }
        .analytics-chart-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: #334155;
            margin-bottom: 0.25rem;
        }
        .analytics-chart-note {
            font-size: 0.72rem;
            color: #64748b;
            margin-bottom: 0.55rem;
        }
        .analytics-bar-stack {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        .analytics-bar-row {
            display: grid;
            grid-template-columns: 72px 1fr auto;
            gap: 0.4rem;
            align-items: center;
            font-size: 0.72rem;
            color: #475569;
        }
        .analytics-bar-track {
            height: 9px;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.2);
            overflow: hidden;
        }
        .analytics-bar-fill {
            height: 100%;
            width: 0;
            border-radius: 999px;
            animation: smoothGrow 850ms cubic-bezier(.2,.8,.2,1) forwards;
        }
        .analytics-line-svg {
            width: 100%;
            height: 140px;
            overflow: visible;
        }
        .analytics-line-path {
            fill: none;
            stroke: #3b82f6;
            stroke-width: 3;
            stroke-linecap: round;
            stroke-linejoin: round;
            stroke-dasharray: 1000;
            stroke-dashoffset: 1000;
            animation: drawLine 1200ms ease forwards;
        }
        .analytics-line-point {
            fill: #2563eb;
            opacity: 0;
            animation: fadePoint 380ms ease forwards;
        }
        @keyframes smoothGrow {
            from { width: 0; }
            to { width: var(--target-width, 0%); }
        }
        @keyframes drawLine {
            to { stroke-dashoffset: 0; }
        }
        @keyframes fadePoint {
            to { opacity: 1; }
        }
        .analytics-recent-list div[data-testid="stButton"] > button {
            background: rgba(248,250,252,0.4);
            border: 1px solid rgba(148, 163, 184, 0.34);
            text-align: left;
            justify-content: flex-start;
            padding-left: 0.7rem;
        }
        .analytics-recent-list div[data-testid="stButton"] > button:hover {
            border-color: rgba(59,130,246,0.5);
            background: rgba(239,246,255,0.7);
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 10px;
            border: 1px solid var(--border);
            background: var(--bg-secondary);
            color: var(--text-primary);
            min-height: 120px !important;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            border-radius: 10px;
            border: 1px solid var(--border);
            background: #ffffff;
            color: var(--text-primary);
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] span {
            color: var(--text-primary);
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {
            border-color: #93c5fd;
            box-shadow: 0 0 0 2px rgba(147, 197, 253, 0.25);
        }
        div[data-testid="stButton"] > button {
            border-radius: 8px;
            font-weight: 600;
            height: 2.2rem;
            background: #ffffff;
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        .mini-note {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.2rem;
            margin-bottom: 0.45rem;
        }
        @media (max-width: 1200px) {
            .analytics-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
            .analytics-subgrid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 760px) {
            .analytics-grid,
            .analytics-subgrid,
            .analytics-chart-grid {
                grid-template-columns: repeat(1, minmax(0, 1fr));
            }
        }
        .queue-item-row {
            margin: 0.1rem 0;
            border-radius: 9px;
        }
        .queue-ticket-button div[data-testid="stButton"] > button {
            border-radius: 9px;
            border: 1px solid var(--ticket-border, transparent);
            min-height: 38px;
            padding: 0.38rem 0.5rem;
            text-align: left;
            font-size: 0.81rem;
            font-weight: 500;
            box-shadow: none;
            transition: all 120ms ease-in-out;
            background: var(--ticket-bg, #ffffff) !important;
            color: var(--ticket-text, var(--text-primary)) !important;
            white-space: normal;
        }
        .queue-ticket-button div[data-testid="stButton"] > button:hover {
            transform: translateY(-1px);
            filter: brightness(0.96);
        }
        .queue-ticket-button.selected div[data-testid="stButton"] > button {
            border-color: var(--ticket-ring, var(--accent));
            box-shadow: inset 0 0 0 1px var(--ticket-ring-soft, rgba(59, 130, 246, 0.25));
            background: var(--ticket-selected-bg, var(--ticket-bg, #ffffff)) !important;
            color: var(--ticket-selected-text, var(--ticket-text, var(--text-primary))) !important;
        }
        .queue-move-control {
            margin-top: 0.5rem;
        }
        .activity-log-list {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        .activity-log-item {
            border: 1px solid var(--border);
            background: var(--bg-tertiary);
            border-radius: 10px;
            padding: 0.55rem 0.65rem;
        }
        .activity-log-meta {
            font-size: 0.74rem;
            color: var(--text-muted);
            margin-bottom: 0.15rem;
        }
        .activity-log-action {
            font-size: 0.84rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.1rem;
        }
        .activity-log-details {
            font-size: 0.82rem;
            color: #334155;
            line-height: 1.35;
        }
        .queue-section-title-lg {
            font-size: 1.9rem;
            line-height: 1.15;
            font-weight: 800;
            margin: 0.2rem 0 0.35rem;
            color: #0f172a;
            letter-spacing: -0.02em;
        }
        .queue-section-title-sm {
            font-size: 1rem;
            line-height: 1.2;
            font-weight: 700;
            margin: 0.25rem 0 0.2rem;
            color: #334155;
        }
        .queue-shell {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 5px 16px rgba(15, 23, 42, 0.05);
            padding: 0.5rem 0.55rem;
            margin-bottom: 0.8rem;
        }
        .queue-head-row {
            display: grid;
            grid-template-columns: 0.8fr 4fr 1.4fr 1.1fr;
            gap: 0.55rem;
            padding: 0.22rem 0.4rem 0.35rem;
            border-bottom: 1px solid #eef2f7;
            color: #64748b;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-bottom: 0.22rem;
        }
        .priority-dot {
            display: inline-block;
            border-radius: 999px;
            padding: 0.1rem 0.42rem;
            font-size: 0.66rem;
            font-weight: 700;
            line-height: 1.35;
            border: 1px solid transparent;
        }
        .priority-high {
            background: #fee2e2;
            color: #991b1b;
            border-color: #fecaca;
        }
        .priority-medium {
            background: #fef3c7;
            color: #92400e;
            border-color: #fde68a;
        }
        .priority-low {
            background: #e0f2fe;
            color: #075985;
            border-color: #bae6fd;
        }
        .queue-title {
            font-size: 0.79rem;
            font-weight: 650;
            color: #0f172a;
            line-height: 1.2;
            margin-top: 0.08rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .queue-meta {
            font-size: 0.68rem;
            color: #94a3b8;
            margin-top: 0.06rem;
        }
        .queue-status {
            font-size: 0.69rem;
            font-weight: 600;
            color: #475569;
            margin-top: 0.12rem;
        }
        .queue-updated {
            font-size: 0.68rem;
            color: #94a3b8;
            margin-top: 0.14rem;
        }
        .queue-shell div[data-testid="stButton"] > button {
            white-space: nowrap;
        }
        section[data-testid="stSidebar"] div[data-baseweb="radio"] label {
            padding: 0.32rem 0.42rem;
            border-radius: 8px;
            margin-bottom: 0.16rem;
            border: 1px solid transparent;
        }
        section[data-testid="stSidebar"] div[data-baseweb="radio"] label:has(input:checked) {
            background: #eef4ff;
            border-color: #dbeafe;
        }
        .scroll-panel {
            padding-right: 0.2rem;
        }
        .resolution-scroll {
            max-height: 260px;
            overflow-y: auto;
            padding-right: 0.25rem;
        }
        @keyframes floatGlow {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(10px, -12px) scale(1.06); }
        }
        @keyframes pulsePill {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.05); }
            50% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.01); }
        }
        .three-col-header {
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding-bottom: 0.22rem;
        }
        .three-col-header::after {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: -2px;
            height: 2px;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(59,130,246,0.85), rgba(59,130,246,0.1));
            transform-origin: left;
            animation: headerSweep 2.8s ease-in-out infinite;
        }
        @keyframes headerSweep {
            0%, 100% { transform: scaleX(0.35); opacity: 0.65; }
            50% { transform: scaleX(1); opacity: 1; }
        }
        @media (max-width: 1100px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            section[data-testid="stSidebar"] {
                min-width: 250px !important;
                max-width: 250px !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

URGENCY_RANK = {"high": 0, "medium": 1, "low": 2}
STATUS_STAGES = ("new", "in_progress", "blocked", "completed")
STATUS_SORT_ORDER = {"new": 0, "in_progress": 1, "blocked": 2, "completed": 3, "deleted": 4}
STATUS_LABELS = {
    "new": "New",
    "in_progress": "In Progress",
    "blocked": "Blocked",
    "completed": "Completed",
}
PROGRESS_OPTIONS = ("in_progress", "blocked", "completed")
OPEN_STATUSES = ("new", "in_progress", "blocked")
DEFAULT_PRELOADED_TICKETS = [
    {
        "title": "System Down – Unable to Submit Prior Auth",
        "description": "User cannot access the portal and receives a 500 error during submission.",
        "impact": "Authorizations blocked across providers",
        "urgency": "high",
        "status": "blocked",
    },
    {
        "title": "Urgent Surgery Auth Missing",
        "description": "Scheduled procedure is today and no authorization can be found in the case.",
        "impact": "Same-day surgery at risk",
        "urgency": "high",
        "status": "in_progress",
    },
    {
        "title": "Incorrect Denial – Patient Critical",
        "description": "System auto-denied request that appears to meet approval criteria.",
        "impact": "Potential delay in critical care",
        "urgency": "high",
        "status": "new",
    },
    {
        "title": "Portal Timeout During Submission",
        "description": "Prior auth request times out during submit and does not complete.",
        "impact": "Repeated submission attempts failing",
        "urgency": "high",
        "status": "in_progress",
    },
    {
        "title": "Duplicate Auth Created",
        "description": "Two authorizations were created for the same request and patient.",
        "impact": "Risk of payer confusion and rework",
        "urgency": "high",
        "status": "completed",
    },
    {
        "title": "Eligibility Not Loading",
        "description": "User cannot verify coverage because eligibility module does not load.",
        "impact": "Unable to validate medical necessity workflow",
        "urgency": "high",
        "status": "blocked",
    },
    {
        "title": "Provider Locked Out",
        "description": "Provider account is denied after login attempts and cannot access queue.",
        "impact": "Urgent access interruption",
        "urgency": "high",
        "status": "completed",
    },
    {
        "title": "Authorization Status Not Updating",
        "description": "Request still shows pending even after payer indicates approval.",
        "impact": "Clinical scheduling stalled",
        "urgency": "high",
        "status": "in_progress",
    },
    {
        "title": "Clinical Docs Not Uploading",
        "description": "Required attachments fail to upload during request submission.",
        "impact": "Cannot finalize clinical packet",
        "urgency": "high",
        "status": "new",
    },
    {
        "title": "Incorrect CPT Code Applied",
        "description": "System mapped the procedure to the wrong CPT code automatically.",
        "impact": "High denial risk on urgent case",
        "urgency": "high",
        "status": "blocked",
    },
    {
        "title": "Payer API Failure",
        "description": "Payer integration is returning no response for authorization checks.",
        "impact": "External dependency outage",
        "urgency": "high",
        "status": "in_progress",
    },
    {
        "title": "Urgent Appeal Submission Blocked",
        "description": "Appeal action button is not working on high-priority denial.",
        "impact": "Time-sensitive appeal delayed",
        "urgency": "high",
        "status": "new",
    },
    {
        "title": "Patient Record Not Found",
        "description": "Patient is present in EHR but missing in triage system search.",
        "impact": "Urgent authorization cannot proceed",
        "urgency": "high",
        "status": "completed",
    },
    {
        "title": "Auto-Approval Not Triggering",
        "description": "Request meets configured rules but remains pending with no auto-approval.",
        "impact": "Potentially avoidable treatment delays",
        "urgency": "high",
        "status": "in_progress",
    },
    {
        "title": "Fax Integration Down",
        "description": "Incoming faxes are not attaching to active authorization cases.",
        "impact": "Clinical documents missing from review",
        "urgency": "high",
        "status": "deleted",
    },
    {
        "title": "Slow Response Time",
        "description": "Portal pages are taking more than 10 seconds to load.",
        "impact": "Productivity degradation for intake staff",
        "urgency": "medium",
        "status": "in_progress",
    },
    {
        "title": "Auth Status Delay",
        "description": "Status updates lag behind payer responses for active requests.",
        "impact": "Operational confusion and follow-up calls",
        "urgency": "medium",
        "status": "new",
    },
    {
        "title": "Incorrect Provider Info",
        "description": "Wrong NPI appears on authorization request summary.",
        "impact": "May require correction before submission",
        "urgency": "medium",
        "status": "completed",
    },
    {
        "title": "Missing Clinical Fields",
        "description": "Required clinical input fields are not visible in the form.",
        "impact": "Submissions paused pending form fix",
        "urgency": "medium",
        "status": "blocked",
    },
    {
        "title": "Notification Not Sent",
        "description": "Provider did not receive expected approval email notification.",
        "impact": "Communication gap for care teams",
        "urgency": "medium",
        "status": "in_progress",
    },
    {
        "title": "Appeal Status Confusing",
        "description": "Displayed appeal status is unclear and causing repeated questions.",
        "impact": "Support volume increase",
        "urgency": "medium",
        "status": "new",
    },
    {
        "title": "Multiple Patient Matches",
        "description": "Search returns duplicate patient candidates for one member.",
        "impact": "Risk of selecting wrong chart",
        "urgency": "medium",
        "status": "completed",
    },
    {
        "title": "Authorization Expiring Early",
        "description": "Authorization end date appears earlier than payer-confirmed window.",
        "impact": "Potential avoidable resubmissions",
        "urgency": "medium",
        "status": "blocked",
    },
    {
        "title": "Dropdown Not Loading",
        "description": "Payer dropdown list does not populate in intake workflow.",
        "impact": "Users cannot complete required selection",
        "urgency": "medium",
        "status": "in_progress",
    },
    {
        "title": "Search Function Slow",
        "description": "Ticket and member search is taking too long to return results.",
        "impact": "Queue throughput reduced",
        "urgency": "medium",
        "status": "new",
    },
    {
        "title": "Partial Submission Saved",
        "description": "System saved an incomplete request unexpectedly during entry.",
        "impact": "Requires manual cleanup before routing",
        "urgency": "medium",
        "status": "completed",
    },
    {
        "title": "Incorrect Diagnosis Code Mapping",
        "description": "ICD-10 mapping appears mismatched to selected diagnosis.",
        "impact": "Potential medical necessity mismatch",
        "urgency": "medium",
        "status": "in_progress",
    },
    {
        "title": "UI Layout Issue",
        "description": "Form fields overlap on screen making some entries hard to read.",
        "impact": "Workflow usability degraded",
        "urgency": "medium",
        "status": "new",
    },
    {
        "title": "Export Report Error",
        "description": "CSV export fails from analytics report with an error message.",
        "impact": "Reporting task blocked",
        "urgency": "medium",
        "status": "blocked",
    },
    {
        "title": "Notes Not Saving",
        "description": "User-entered notes disappear after navigating between screens.",
        "impact": "Loss of triage context",
        "urgency": "medium",
        "status": "in_progress",
    },
    {
        "title": "Authorization History Missing",
        "description": "Previous workflow actions are not visible in history timeline.",
        "impact": "Audit trail appears incomplete",
        "urgency": "medium",
        "status": "completed",
    },
    {
        "title": "Filter Not Working",
        "description": "Status filter does not update queue results when selected.",
        "impact": "Users cannot isolate work efficiently",
        "urgency": "medium",
        "status": "new",
    },
    {
        "title": "Session Timeout Too Short",
        "description": "System signs users out after about five minutes of inactivity.",
        "impact": "Frequent interruptions for staff",
        "urgency": "medium",
        "status": "blocked",
    },
    {
        "title": "Duplicate Notifications",
        "description": "Same alert is being sent multiple times for one status change.",
        "impact": "Notification fatigue",
        "urgency": "medium",
        "status": "in_progress",
    },
    {
        "title": "Task Queue Not Updating",
        "description": "Completed items continue to display as active in queue.",
        "impact": "Queue metrics skewed",
        "urgency": "medium",
        "status": "deleted",
    },
    {
        "title": "Typo in UI Label",
        "description": "Minor spelling error found in prior auth request label.",
        "impact": "Cosmetic issue only",
        "urgency": "low",
        "status": "new",
    },
    {
        "title": "Color Contrast Issue",
        "description": "Some UI text has low contrast and is difficult to read.",
        "impact": "Accessibility concern for users",
        "urgency": "low",
        "status": "in_progress",
    },
    {
        "title": "Tooltip Missing",
        "description": "Help tooltip is not appearing for a non-critical form field.",
        "impact": "Minor usability friction",
        "urgency": "low",
        "status": "completed",
    },
    {
        "title": "Request for Feature",
        "description": "User requested bulk document upload capability.",
        "impact": "Feature enhancement request",
        "urgency": "low",
        "status": "new",
    },
    {
        "title": "Dashboard Layout Suggestion",
        "description": "User suggested readability improvements for dashboard arrangement.",
        "impact": "Product feedback for future iteration",
        "urgency": "low",
        "status": "completed",
    },
    {
        "title": "Slow Report Generation",
        "description": "Non-critical report generation is slower than expected.",
        "impact": "Background reporting delay",
        "urgency": "low",
        "status": "in_progress",
    },
    {
        "title": "Minor Alignment Issue",
        "description": "One action button appears slightly misaligned in the form.",
        "impact": "Small visual inconsistency",
        "urgency": "low",
        "status": "new",
    },
    {
        "title": "Profile Update Delay",
        "description": "Profile changes take extra time to appear after saving.",
        "impact": "Low-severity sync delay",
        "urgency": "low",
        "status": "blocked",
    },
    {
        "title": "Help Link Broken",
        "description": "Help center link redirects to a non-working destination.",
        "impact": "Self-service guidance unavailable",
        "urgency": "low",
        "status": "completed",
    },
    {
        "title": "Email Formatting Issue",
        "description": "Notification email layout appears misformatted in inbox.",
        "impact": "Readability issue in communications",
        "urgency": "low",
        "status": "new",
    },
    {
        "title": "Pagination Confusing",
        "description": "Pagination behavior is unclear when navigating ticket lists.",
        "impact": "Minor navigation friction",
        "urgency": "low",
        "status": "in_progress",
    },
    {
        "title": "Auto-fill Not Working",
        "description": "Known values are not auto-filling in optional fields.",
        "impact": "Extra manual entry required",
        "urgency": "low",
        "status": "completed",
    },
    {
        "title": "Saved Filters Reset",
        "description": "User filter preferences are not retained between sessions.",
        "impact": "Inconvenience for repeat users",
        "urgency": "low",
        "status": "new",
    },
    {
        "title": "Mobile View Issue",
        "description": "Layout breaks on phone-sized screens in non-critical views.",
        "impact": "Mobile usability issue",
        "urgency": "low",
        "status": "blocked",
    },
    {
        "title": "General Feedback",
        "description": "User submitted general UI and workflow improvement feedback.",
        "impact": "No immediate operational impact",
        "urgency": "low",
        "status": "deleted",
    },
]


def load_tickets() -> list[dict]:
    # Demo mode: initialize each session with a curated default queue.
    window_start = datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 4, 30, 23, 59, 59, tzinfo=timezone.utc)
    total_seconds = int((window_end - window_start).total_seconds())
    rng = random.Random()
    preloaded_tickets: list[dict] = []
    for index, template in enumerate(DEFAULT_PRELOADED_TICKETS, start=1):
        created_at = (
            window_start + timedelta(seconds=rng.randint(0, total_seconds))
        ).replace(microsecond=0)
        ai_processed_at = created_at + timedelta(minutes=rng.randint(1, 45))
        preloaded_tickets.append(
            {
                "saved_id": f"{index:03d}",
                "created_at": created_at.isoformat(),
                "status": template.get("status", "new"),
                "message": (
                    f"Title: {template['title']}\n"
                    f"Description: {template['description']}\n"
                    f"Impact: {template['impact']}\n"
                    f"Urgency: {template['urgency'].title()}"
                ),
                "classification": "ticket",
                "ticket": {
                    "ticketId": f"{index:03d}",
                    "title": template["title"],
                    "urgency": template["urgency"],
                },
                "resolution": (
                    "Root Cause: Intake issue requires support review.\n"
                    "Recommended Next Steps: Confirm payer and provider context, "
                    "validate request details, then guide user through correction.\n"
                    "Suggested Response to Customer: We have logged your request and "
                    "are reviewing the details to help you complete prior auth submission."
                ),
                "activity_log": [
                    make_log_entry(
                        actor="system",
                        action_type="Request created",
                        details=f"Ticket {index:03d} was created in the triage queue.",
                        timestamp=created_at.isoformat(),
                    ),
                    make_log_entry(
                        actor="ai",
                        action_type="AI triage completed",
                        details="Ticket was analyzed and added to the triage queue.",
                        timestamp=ai_processed_at.isoformat(),
                    ),
                ],
            }
        )
    return preloaded_tickets


def save_tickets(tickets: list[dict]) -> None:
    # Demo mode: in-memory only, intentionally no-op.
    return None


def save_closed_tickets(tickets: list[dict]) -> None:
    # Demo mode: in-memory only, intentionally no-op.
    return None


def load_closed_tickets() -> list[dict]:
    # Demo mode: do not persist tickets between sessions.
    return []


def save_deleted_tickets(tickets: list[dict]) -> None:
    # Demo mode: in-memory only, intentionally no-op.
    return None


def load_deleted_tickets() -> list[dict]:
    # Demo mode: do not persist tickets between sessions.
    return []


def rank_tickets(tickets: list[dict]) -> list[dict]:
    # Priority order: urgency first, then workflow status, then oldest first.
    return sorted(
        tickets,
        key=lambda t: (
            URGENCY_RANK.get((t.get("ticket") or {}).get("urgency", "medium").lower(), 1),
            STATUS_SORT_ORDER.get(normalize_status(t.get("status")), 5),
            t.get("created_at", ""),
        ),
        reverse=False,
    )


def get_completed_tickets(tickets: list[dict]) -> list[dict]:
    return [ticket for ticket in tickets if normalize_status(ticket.get("status")) == "completed"]


def normalize_urgency(urgency: str | None) -> str:
    normalized = (urgency or "").strip().lower()
    return normalized if normalized in {"low", "medium", "high"} else "medium"


def normalize_status(status: str | None) -> str:
    normalized = (status or "").strip().lower()
    if normalized == "open":
        return "new"
    if normalized in {"deleted", "spam"}:
        return "deleted"
    if normalized in {"closed", "done"}:
        return "completed"
    return normalized if normalized in STATUS_STAGES else "new"


def ensure_unique_ticket_id(ticket_id: str | None, existing_tickets: list[dict]) -> str:
    # Use a simple 3-digit sequence (001, 002, ...) across the full session queue.
    numeric_ids: set[int] = set()
    existing_ids = {str(entry.get("saved_id", "")).strip() for entry in existing_tickets}

    for existing_id in existing_ids:
        if re.fullmatch(r"\d{3,}", existing_id):
            numeric_ids.add(int(existing_id))

    requested_id = (ticket_id or "").strip()
    if re.fullmatch(r"\d{3,}", requested_id):
        requested_value = int(requested_id)
        if requested_value not in numeric_ids:
            return f"{requested_value:03d}"

    next_id = (max(numeric_ids) + 1) if numeric_ids else 1
    while f"{next_id:03d}" in existing_ids:
        next_id += 1
    return f"{next_id:03d}"


def clean_ticket_title(title: str | None) -> str:
    cleaned = (title or "").strip()
    for marker in ("🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫", "⬛", "⬜", "◼", "◻", "■", "□"):
        if cleaned.startswith(marker):
            cleaned = cleaned[len(marker):].strip(" :-")
    return cleaned or "Untitled ticket"


def make_log_entry(actor: str, action_type: str, details: str, timestamp: str | None = None) -> dict:
    return {
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "actor": actor.strip().lower(),
        "action_type": action_type.strip(),
        "details": details.strip(),
    }


def ensure_activity_log(ticket_entry: dict) -> list[dict]:
    existing = ticket_entry.get("activity_log")
    if isinstance(existing, list):
        return existing

    ticket_id = ticket_entry.get("saved_id", "N/A")
    created_at = ticket_entry.get("created_at") or datetime.now(timezone.utc).isoformat()
    ticket_entry["activity_log"] = [
        make_log_entry(
            "system",
            "Request created",
            f"Ticket {ticket_id} was created and added to triage.",
            timestamp=created_at,
        )
    ]
    return ticket_entry["activity_log"]


def append_activity_log(ticket_entry: dict, actor: str, action_type: str, details: str) -> None:
    log = ensure_activity_log(ticket_entry)
    log.append(make_log_entry(actor=actor, action_type=action_type, details=details))


def urgency_badge_html(urgency: str) -> str:
    urgency = normalize_urgency(urgency)
    css_class = {"low": "badge-low", "medium": "badge-medium", "high": "badge-high"}.get(
        urgency,
        "badge-medium",
    )
    return f'<span class="badge {css_class}">{urgency.upper()}</span>'


def classification_badge_html(classification: str) -> str:
    normalized = (classification or "").strip().lower()
    css_class = "badge-spam" if normalized == "spam" else "badge-medium"
    label = "SPAM" if normalized == "spam" else "TICKET"
    return f'<span class="badge {css_class}">{label}</span>'


def parse_resolution_text(resolution: str) -> tuple[str, str, str]:
    # Best-effort parser for semi-structured agent text output sections.
    root_cause = ""
    next_steps = ""
    suggested_response = ""

    if "Root Cause:" in resolution:
        after = resolution.split("Root Cause:", 1)[1]
        if "Recommended Next Steps" in after:
            root_cause, after = after.split("Recommended Next Steps", 1)
        else:
            root_cause = after

    if "Recommended Next Steps" in resolution:
        after = resolution.split("Recommended Next Steps", 1)[1]
        if "Suggested Response" in after:
            next_steps, after = after.split("Suggested Response", 1)
        else:
            next_steps = after

    if "Suggested Response" in resolution:
        suggested_response = resolution.split("Suggested Response", 1)[1]

    root_cause = (
        root_cause.replace("for Support Team:", "").replace("to Customer:", "").strip(" :\n")
    )
    next_steps = (
        next_steps.replace("for Support Team:", "").replace("to Customer:", "").strip(" :\n")
    )
    suggested_response = suggested_response.replace("to Customer:", "").strip(" :\n")

    if not root_cause and not next_steps and not suggested_response:
        return "", resolution.strip(), ""

    return root_cause.strip(), next_steps.strip(), suggested_response.strip()


def render_result(
    result: dict,
    submitted_request: str = "",
    default_urgency: str = "medium",
    default_status: str = "in_progress",
    default_classification: str = "ticket",
    key_prefix: str = "overview",
) -> tuple[str, str, str, str]:
    ticket = result.get("ticket") or {}
    with st.container():
        st.markdown('<div class="section-title">Ticket Info</div>', unsafe_allow_html=True)
        edited_title = st.text_input(
            "Title",
            value=clean_ticket_title(ticket.get("title")),
            key=f"{key_prefix}_title_{ticket.get('ticketId', 'unknown')}",
        )
        col_classification, col_urgency, col_status = st.columns(3, gap="small")
        with col_classification:
            selected_classification = st.selectbox(
                "Classification",
                options=["ticket", "spam"],
                index=0 if default_classification == "ticket" else 1,
                format_func=lambda classification: classification.title(),
                key=f"{key_prefix}_classification_{ticket.get('ticketId', 'unknown')}",
            )
        with col_urgency:
            urgency_options = ["low", "medium", "high"]
            selected_urgency = st.selectbox(
                "Urgency",
                options=urgency_options,
                index=urgency_options.index(default_urgency),
                format_func=lambda urgency: urgency.title(),
                key=f"{key_prefix}_urgency_{ticket.get('ticketId', 'unknown')}",
            )
        with col_status:
            selected_status = st.selectbox(
                "Status",
                options=list(PROGRESS_OPTIONS),
                index=list(PROGRESS_OPTIONS).index(default_status),
                format_func=lambda status: STATUS_LABELS[status],
                key=f"{key_prefix}_status_{ticket.get('ticketId', 'unknown')}",
            )
        st.caption(f"Ticket ID: {ticket.get('ticketId', 'N/A')}")

    root_cause, next_steps, suggested_response = parse_resolution_text(result["resolution"])

    with st.container():
        st.markdown('<div class="section-title">Resolution</div>', unsafe_allow_html=True)
        st.write(result["resolution"])

    with st.container():
        st.markdown('<div class="section-title">Likely Root Cause</div>', unsafe_allow_html=True)
        st.write(root_cause if root_cause else "No root cause was extracted.")

    with st.container():
        st.markdown('<div class="section-title">Recommended Next Steps</div>', unsafe_allow_html=True)
        st.write(next_steps if next_steps else "No additional next steps were provided.")
        if suggested_response:
            st.markdown('<div class="section-label">Suggested response</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="response-box">{html.escape(suggested_response)}</div>',
                unsafe_allow_html=True,
            )

    if submitted_request:
        st.markdown('<div class="section-title">Submitted Request</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="response-box">{html.escape(submitted_request)}</div>',
            unsafe_allow_html=True,
        )

    return selected_urgency, selected_status, selected_classification, edited_title.strip()


def render_empty_result_placeholder() -> None:
    st.markdown('<div class="section-title">Ticket details</div>', unsafe_allow_html=True)
    st.caption("Resolution output will appear here.")
    st.markdown(
        '<div class="mini-note">Choose a ticket from the queue or run a new triage search to populate this panel.</div>',
        unsafe_allow_html=True,
    )


def render_activity_log(ticket_entry: dict, show_title: bool = True) -> None:
    entries = ensure_activity_log(ticket_entry)
    sorted_entries = sorted(
        entries,
        key=lambda entry: entry.get("timestamp", ""),
        reverse=True,
    )
    if show_title:
        st.markdown('<div class="section-title">Activity Log</div>', unsafe_allow_html=True)
    if not sorted_entries:
        st.caption("No activity recorded yet.")
    else:
        st.markdown('<div class="activity-log-list">', unsafe_allow_html=True)
        for entry in sorted_entries:
            timestamp = entry.get("timestamp", "")
            try:
                parsed_ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                display_ts = parsed_ts.strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                display_ts = timestamp or "Unknown time"
            actor = (entry.get("actor") or "system").replace("_", " ").upper()
            action_type = entry.get("action_type") or "Activity updated"
            details = entry.get("details") or ""
            st.markdown(
                (
                    '<div class="activity-log-item">'
                    f'<div class="activity-log-meta">{html.escape(display_ts)} · {html.escape(actor)}</div>'
                    f'<div class="activity-log-action">{html.escape(action_type)}</div>'
                    f'<div class="activity-log-details">{html.escape(details)}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_selected_ticket_details(
    all_tickets: list[dict],
    show_queue_move: bool = False,
    ticket_queue_label_fn=None,
    move_ticket_fn=None,
    show_activity_log: bool = True,
) -> None:
    if st.session_state.selected_ticket_id:
        selected = next(
            (
                entry
                for entry in all_tickets
                if entry.get("saved_id") == st.session_state.selected_ticket_id
            ),
            None,
        )
        if selected:
            selected_ticket = selected.get("ticket") or {}
            current_urgency = normalize_urgency(selected_ticket.get("urgency"))
            current_status = normalize_status(selected.get("status"))
            default_status = current_status if current_status in PROGRESS_OPTIONS else "in_progress"
            default_urgency = current_urgency if current_urgency in {"low", "medium", "high"} else "medium"
            current_classification = (
                (selected.get("classification") or "ticket").strip().lower()
            )
            default_classification = "spam" if current_classification == "spam" else "ticket"

            urgency_choice, progress_choice, classification_choice, edited_title = render_result(
                {
                    "classification": default_classification,
                    "ticket": selected_ticket,
                    "resolution": selected.get("resolution", ""),
                },
                submitted_request=selected.get("message", ""),
                default_urgency=default_urgency,
                default_status=default_status,
                default_classification=default_classification,
                key_prefix=f"selected_{selected.get('saved_id')}",
            )

            normalized_title = clean_ticket_title(edited_title)
            if (
                urgency_choice != current_urgency
                or progress_choice != current_status
                or classification_choice != default_classification
                or normalized_title != clean_ticket_title(selected_ticket.get("title"))
            ):
                if urgency_choice != current_urgency:
                    append_activity_log(
                        selected,
                        actor="human_agent",
                        action_type="Priority changed",
                        details=f"Urgency changed from {current_urgency} to {urgency_choice}.",
                    )
                if progress_choice != current_status:
                    append_activity_log(
                        selected,
                        actor="human_agent",
                        action_type="Status changed",
                        details=f"Status changed from {current_status} to {progress_choice}.",
                    )
                if classification_choice != default_classification:
                    append_activity_log(
                        selected,
                        actor="human_agent",
                        action_type="Classification changed",
                        details=f"Classification changed from {default_classification} to {classification_choice}.",
                    )
                if normalized_title != clean_ticket_title(selected_ticket.get("title")):
                    append_activity_log(
                        selected,
                        actor="human_agent",
                        action_type="Title updated",
                        details=f"Title updated to '{normalized_title}'.",
                    )
                selected_ticket["urgency"] = urgency_choice
                selected_ticket["title"] = normalized_title
                selected["status"] = progress_choice
                selected["classification"] = classification_choice
                if progress_choice == "completed":
                    st.session_state.open_tickets = [
                        t
                        for t in st.session_state.open_tickets
                        if t.get("saved_id") != selected.get("saved_id")
                    ]
                    if not any(
                        t.get("saved_id") == selected.get("saved_id")
                        for t in st.session_state.closed_tickets
                    ):
                        st.session_state.closed_tickets.append(selected)
                    st.session_state.deleted_tickets = [
                        t
                        for t in st.session_state.deleted_tickets
                        if t.get("saved_id") != selected.get("saved_id")
                    ]
                else:
                    st.session_state.closed_tickets = [
                        t
                        for t in st.session_state.closed_tickets
                        if t.get("saved_id") != selected.get("saved_id")
                    ]
                    st.session_state.deleted_tickets = [
                        t
                        for t in st.session_state.deleted_tickets
                        if t.get("saved_id") != selected.get("saved_id")
                    ]
                    if not any(
                        t.get("saved_id") == selected.get("saved_id")
                        for t in st.session_state.open_tickets
                    ):
                        st.session_state.open_tickets.append(selected)
                persist_ticket_state()
                st.rerun()

            if show_queue_move and ticket_queue_label_fn and move_ticket_fn:
                queue_targets = {
                    "Open Queue": "open",
                    "Blocked Queue": "blocked",
                    "Archived Queue": "archived",
                    "Deleted / Spam": "deleted",
                }
                queue_labels = list(queue_targets.keys())
                current_label = ticket_queue_label_fn(selected, "details")
                st.markdown('<div class="queue-move-control">', unsafe_allow_html=True)
                selected_label = st.selectbox(
                    "Move ticket to queue",
                    options=queue_labels,
                    index=queue_labels.index(current_label),
                    key=f"move_details_{selected.get('saved_id')}",
                )
                if selected_label != current_label:
                    move_ticket_fn(selected, queue_targets[selected_label])
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            if show_activity_log:
                render_activity_log(selected)
        else:
            render_empty_result_placeholder()
    else:
        render_empty_result_placeholder()


def get_selected_ticket(all_tickets: list[dict]) -> dict | None:
    selected_id = st.session_state.selected_ticket_id
    if not selected_id:
        return None
    return next((entry for entry in all_tickets if entry.get("saved_id") == selected_id), None)


def track_recent_ticket_view(ticket_id: str | None) -> None:
    if not ticket_id:
        return
    recent_views = st.session_state.setdefault("recent_viewed_ticket_ids", [])
    recent_views = [existing_id for existing_id in recent_views if existing_id != ticket_id]
    recent_views.insert(0, ticket_id)
    st.session_state.recent_viewed_ticket_ids = recent_views[:5]


def format_relative_time(iso_timestamp: str | None) -> str:
    if not iso_timestamp:
        return "—"
    try:
        created_dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return "—"
    delta = datetime.now(timezone.utc) - created_dt
    total_minutes = max(1, int(delta.total_seconds() // 60))
    if total_minutes < 60:
        return f"{total_minutes}m ago"
    total_hours = total_minutes // 60
    if total_hours < 24:
        return f"{total_hours}h ago"
    return f"{total_hours // 24}d ago"


def render_compact_queue_rows(queue_key: str, tickets: list[dict], scope: str) -> None:
    st.markdown(
        '<div class="queue-head-row"><div>Priority</div><div>Ticket</div><div>Status</div><div>Updated</div></div>',
        unsafe_allow_html=True,
    )
    for idx, ticket in enumerate(tickets):
        ticket_id = ticket.get("saved_id", "")
        ticket_data = ticket.get("ticket") or {}
        urgency = normalize_urgency(ticket_data.get("urgency"))
        urgency_label = urgency.title()
        priority_class = {
            "high": "priority-dot priority-high",
            "medium": "priority-dot priority-medium",
            "low": "priority-dot priority-low",
        }.get(urgency, "priority-dot")
        title = clean_ticket_title(ticket_data.get("title"))
        status_label = STATUS_LABELS.get(normalize_status(ticket.get("status")), "Open")
        updated_label = format_relative_time(ticket.get("created_at"))
        column_widths = [0.95, 3.95, 1.2, 1.25] if scope == "sidebar" else [0.85, 4.2, 1.5, 1.15]

        with st.container():
            c1, c2, c3, c4 = st.columns(column_widths, gap="small")
            with c1:
                st.markdown(
                    f'<span class="{priority_class}">{html.escape(urgency_label)}</span>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f'<div class="queue-title">{html.escape(title)}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="queue-meta">#{html.escape(str(ticket_id or "N/A"))}</div>',
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(f'<div class="queue-status">{html.escape(status_label)}</div>', unsafe_allow_html=True)
            with c4:
                button_key = f"open_{scope}_{queue_key}_{ticket_id or idx}"
                if st.button(updated_label, key=button_key, use_container_width=True):
                    st.session_state.selected_ticket_id = ticket_id
                    track_recent_ticket_view(ticket_id)
                    st.session_state.pending_view = "Ticket Desk"
                    st.rerun()


def render_new_ticket_search_panel(form_key: str) -> tuple[bool, str]:
    st.markdown('<div class="three-col-header">🔎 New ticket search</div>', unsafe_allow_html=True)
    with st.form(form_key, clear_on_submit=True):
        message = st.text_area(
            "Incoming support message",
            key=f"message_input_{form_key}",
            height=120,
            placeholder="Paste a support ticket here...",
        )
        submitted = st.form_submit_button("Run triage", type="secondary", use_container_width=False)
    triage_feedback = st.session_state.triage_feedback
    if triage_feedback:
        feedback_type = triage_feedback.get("type", "info")
        feedback_message = triage_feedback.get("message", "")
        if feedback_type == "success":
            st.success(feedback_message)
        elif feedback_type == "error":
            st.error(feedback_message)
        elif feedback_type == "warning":
            st.warning(feedback_message)
        else:
            st.info(feedback_message)
    return submitted, message


def persist_ticket_state() -> None:
    save_tickets(st.session_state.open_tickets)
    save_closed_tickets(st.session_state.closed_tickets)
    save_deleted_tickets(st.session_state.deleted_tickets)


def _build_daily_volume_chart_html(filtered_tickets: list[dict], start_date, end_date) -> str:
    day_span = max(1, (end_date - start_date).days + 1)
    day_counts = [0] * day_span

    for ticket in filtered_tickets:
        created_at = ticket.get("created_at")
        if not created_at:
            continue
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        day_index = (created_dt.date() - start_date).days
        if 0 <= day_index < day_span:
            day_counts[day_index] += 1

    max_count = max(day_counts) if day_counts else 1
    width, height = 560, 128
    left_pad, right_pad, top_pad, bottom_pad = 12, 12, 10, 22
    plot_width = max(1, width - left_pad - right_pad)
    plot_height = max(1, height - top_pad - bottom_pad)

    if day_span == 1:
        x_step = 0
    else:
        x_step = plot_width / (day_span - 1)

    points: list[tuple[float, float, int]] = []
    for idx, count in enumerate(day_counts):
        x = left_pad + (x_step * idx)
        y = top_pad + (plot_height * (1 - (count / max_count if max_count else 0)))
        points.append((x, y, count))

    polyline_points = " ".join(f"{x:.2f},{y:.2f}" for x, y, _ in points)
    circles = []
    for idx, (x, y, count) in enumerate(points):
        circles.append(
            f'<circle class="analytics-line-point" cx="{x:.2f}" cy="{y:.2f}" r="3" '
            f'style="animation-delay:{180 + (idx * 60)}ms;">'
            f'<title>{count} ticket{"s" if count != 1 else ""}</title>'
            f"</circle>"
        )

    line_labels = (
        f'<text x="{left_pad}" y="{height - 4}" font-size="10" fill="#64748b">{start_date.isoformat()}</text>'
        f'<text x="{width - right_pad}" y="{height - 4}" text-anchor="end" font-size="10" fill="#64748b">{end_date.isoformat()}</text>'
    )

    return (
        f'<svg class="analytics-line-svg" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Daily ticket volume from {start_date.isoformat()} to {end_date.isoformat()}">'
        f'<line x1="{left_pad}" y1="{height - bottom_pad}" x2="{width - right_pad}" y2="{height - bottom_pad}" '
        f'stroke="rgba(148,163,184,0.45)" stroke-width="1"/>'
        f'<polyline class="analytics-line-path" points="{polyline_points}"></polyline>'
        f'{"".join(circles)}'
        f"{line_labels}"
        f"</svg>"
    )


def _build_status_distribution_html(filtered_tickets: list[dict]) -> str:
    status_counts = {
        "New": 0,
        "In progress": 0,
        "Blocked": 0,
        "Completed": 0,
        "Deleted": 0,
    }
    status_color = {
        "New": "#3b82f6",
        "In progress": "#6366f1",
        "Blocked": "#f59e0b",
        "Completed": "#10b981",
        "Deleted": "#94a3b8",
    }

    for ticket in filtered_tickets:
        status = normalize_status(ticket.get("status"))
        if status == "new":
            status_counts["New"] += 1
        elif status == "in_progress":
            status_counts["In progress"] += 1
        elif status == "blocked":
            status_counts["Blocked"] += 1
        elif status == "completed":
            status_counts["Completed"] += 1
        else:
            status_counts["Deleted"] += 1

    total = max(1, sum(status_counts.values()))
    rows = []
    for label, count in status_counts.items():
        percentage = (count / total) * 100
        rows.append(
            (
                '<div class="analytics-bar-row">'
                f"<span>{label}</span>"
                '<div class="analytics-bar-track">'
                f'<div class="analytics-bar-fill" style="--target-width:{percentage:.1f}%; background:{status_color[label]};"></div>'
                "</div>"
                f"<span>{count}</span>"
                "</div>"
            )
        )
    return f'<div class="analytics-bar-stack">{"".join(rows)}</div>'


def render_analytics_center(open_tickets: list[dict], closed_tickets: list[dict], deleted_tickets: list[dict]) -> None:
    st.markdown('<div class="three-col-header">📊 Analytics center</div>', unsafe_allow_html=True)

    all_tickets = open_tickets + closed_tickets + deleted_tickets
    dated_tickets: list[tuple[dict, datetime]] = []
    for ticket in all_tickets:
        created_at = ticket.get("created_at")
        if not created_at:
            continue
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        dated_tickets.append((ticket, created_dt))

    if dated_tickets:
        min_created_date = min(created_dt.date() for _, created_dt in dated_tickets)
        max_created_date = max(created_dt.date() for _, created_dt in dated_tickets)
        selected_range = st.date_input(
            "Created date range",
            value=(min_created_date, max_created_date),
            min_value=min_created_date,
            max_value=max_created_date,
            key="analytics_created_date_range",
            help="Filters analytics by ticket created date.",
        )
    else:
        today = datetime.now(timezone.utc).date()
        selected_range = (today, today)
        st.date_input(
            "Created date range",
            value=selected_range,
            key="analytics_created_date_range_empty",
            disabled=True,
            help="No tickets with valid created dates are available.",
        )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date = end_date = selected_range[0] if isinstance(selected_range, tuple) else selected_range

    filtered_tickets: list[dict] = []
    for ticket, created_dt in dated_tickets:
        if start_date <= created_dt.date() <= end_date:
            filtered_tickets.append(ticket)

    filtered_open_tickets = [t for t in filtered_tickets if normalize_status(t.get("status")) in OPEN_STATUSES]
    filtered_closed_tickets = [t for t in filtered_tickets if normalize_status(t.get("status")) == "completed"]
    filtered_deleted_tickets = [t for t in filtered_tickets if normalize_status(t.get("status")) == "deleted"]

    now_utc = datetime.now(timezone.utc)
    total_tickets = len(filtered_tickets)
    active_tickets = len([t for t in filtered_open_tickets if normalize_status(t.get("status")) in {"new", "in_progress"}])
    blocked_tickets = len([t for t in filtered_open_tickets if normalize_status(t.get("status")) == "blocked"])
    archived_tickets = len(filtered_closed_tickets)
    spam_tickets = len([t for t in filtered_deleted_tickets if (t.get("classification") or "").lower() == "spam"])

    high_urgency_open = 0
    triage_duration_minutes: list[float] = []
    stale_ticket_count = 0
    ticket_age_hours: list[float] = []

    for ticket in filtered_tickets:
        status = normalize_status(ticket.get("status"))
        ticket_data = ticket.get("ticket") or {}
        urgency = normalize_urgency(ticket_data.get("urgency"))
        if status in {"new", "in_progress", "blocked"} and urgency == "high":
            high_urgency_open += 1

        created_ts = ticket.get("created_at")
        created_dt = None
        if created_ts:
            try:
                created_dt = datetime.fromisoformat(created_ts.replace("Z", "+00:00"))
                ticket_age_hours.append(max(0.0, (now_utc - created_dt).total_seconds() / 3600))
                if status in {"new", "in_progress", "blocked"} and (now_utc - created_dt) > timedelta(hours=24):
                    stale_ticket_count += 1
            except ValueError:
                created_dt = None

        first_triage_at = None
        for log_entry in ensure_activity_log(ticket):
            action_type = (log_entry.get("action_type") or "").strip().lower()
            if "triage" in action_type:
                first_triage_at = log_entry.get("timestamp")
                break

        if created_dt and first_triage_at:
            try:
                triage_dt = datetime.fromisoformat(first_triage_at.replace("Z", "+00:00"))
                triage_duration_minutes.append(max(0.0, (triage_dt - created_dt).total_seconds() / 60))
            except ValueError:
                continue

    avg_first_triage_minutes = (sum(triage_duration_minutes) / len(triage_duration_minutes)) if triage_duration_minutes else 0.0
    avg_ticket_age_hours = (sum(ticket_age_hours) / len(ticket_age_hours)) if ticket_age_hours else 0.0

    st.markdown('<div class="analytics-shell">', unsafe_allow_html=True)
    st.caption(f"Showing tickets created between {start_date.isoformat()} and {end_date.isoformat()}.")
    st.markdown(
        f"""
        <div class="analytics-grid">
            <div class="analytics-kpi"><div class="analytics-kpi-label">Total tickets</div><div class="analytics-kpi-value">{total_tickets}</div><div class="analytics-kpi-note">Across all queues</div></div>
            <div class="analytics-kpi"><div class="analytics-kpi-label">Active</div><div class="analytics-kpi-value">{active_tickets}</div><div class="analytics-kpi-note">New + in progress</div></div>
            <div class="analytics-kpi"><div class="analytics-kpi-label">Blocked</div><div class="analytics-kpi-value">{blocked_tickets}</div><div class="analytics-kpi-note">Needs external action</div></div>
            <div class="analytics-kpi"><div class="analytics-kpi-label">Archived</div><div class="analytics-kpi-value">{archived_tickets}</div><div class="analytics-kpi-note">Completed tickets</div></div>
            <div class="analytics-kpi"><div class="analytics-kpi-label">Spam</div><div class="analytics-kpi-value">{spam_tickets}</div><div class="analytics-kpi-note">Deleted as spam</div></div>
        </div>
        <div class="analytics-subgrid">
            <div class="analytics-chip"><div class="analytics-chip-label">High urgency open</div><div class="analytics-chip-value">{high_urgency_open}</div></div>
            <div class="analytics-chip"><div class="analytics-chip-label">Avg first triage time</div><div class="analytics-chip-value">{avg_first_triage_minutes:.0f}m</div></div>
            <div class="analytics-chip"><div class="analytics-chip-label">Open > 24h</div><div class="analytics-chip-value">{stale_ticket_count}</div></div>
            <div class="analytics-chip"><div class="analytics-chip-label">Avg ticket age</div><div class="analytics-chip-value">{avg_ticket_age_hours:.1f}h</div></div>
        </div>
        <div class="analytics-chart-grid">
            <div class="analytics-chart-card">
                <div class="analytics-chart-title">Daily ticket volume trend</div>
                <div class="analytics-chart-note">Tickets created per day within selected range.</div>
                {_build_daily_volume_chart_html(filtered_tickets, start_date, end_date)}
            </div>
            <div class="analytics-chart-card">
                <div class="analytics-chart-title">Status distribution</div>
                <div class="analytics-chart-note">Smooth-loading bars for active queue flow.</div>
                {_build_status_distribution_html(filtered_tickets)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    queue_jump_cols = st.columns(5)
    queue_jump_actions = [
        ("Total tickets", "open", "all"),
        ("Active", "open", "all"),
        ("Blocked", "blocked", "all"),
        ("Archived", "archive", "all"),
        ("Spam", "deleted", "spam"),
    ]
    for idx, (label, queue_key, deleted_filter) in enumerate(queue_jump_actions):
        if queue_jump_cols[idx].button(f"Open {label}", key=f"analytics_jump_{label.replace(' ', '_').lower()}", use_container_width=True):
            st.session_state.active_queue = queue_key
            st.session_state.queue_sidebar_filter = deleted_filter
            st.session_state.pending_view = "Triage Workspace"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    urgency_totals = {"high": 0, "medium": 0, "low": 0}
    for ticket in filtered_open_tickets + filtered_closed_tickets:
        urgency = normalize_urgency((ticket.get("ticket") or {}).get("urgency"))
        urgency_totals[urgency] += 1

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ticket mix by urgency</div>', unsafe_allow_html=True)
    mix_cols = st.columns(3)
    for idx, urgency in enumerate(("high", "medium", "low")):
        mix_cols[idx].metric(urgency.title(), urgency_totals[urgency])
    st.progress((urgency_totals["high"] / total_tickets) if total_tickets else 0.0, text="High urgency share")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recent tickets</div>', unsafe_allow_html=True)
    st.markdown('<div class="analytics-recent-list">', unsafe_allow_html=True)
    all_ticket_map = {
        ticket.get("saved_id"): ticket for ticket in filtered_tickets
    }
    recent_viewed_ids = st.session_state.get("recent_viewed_ticket_ids", [])
    recent_viewed_tickets = [all_ticket_map[ticket_id] for ticket_id in recent_viewed_ids if ticket_id in all_ticket_map]

    if not recent_viewed_tickets:
        st.caption("No recently viewed tickets yet. Open a ticket to populate this list.")
    else:
        for ticket in recent_viewed_tickets[:5]:
            ticket_data = ticket.get("ticket") or {}
            title = clean_ticket_title(ticket_data.get("title"))
            status = STATUS_LABELS.get(normalize_status(ticket.get("status")), "Deleted")
            urgency = normalize_urgency(ticket_data.get("urgency"))
            ticket_id = ticket.get("saved_id", "N/A")
            if st.button(
                f"{title} · {status} · {urgency.title()} · #{ticket_id}",
                key=f"analytics_recent_{ticket_id}",
                use_container_width=True,
                help=f"Open ticket #{ticket_id} in Ticket Desk",
            ):
                st.session_state.selected_ticket_id = ticket_id
                track_recent_ticket_view(ticket_id)
                st.session_state.pending_view = "Ticket Desk"
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    export_rows: list[dict] = []
    for ticket in filtered_tickets:
        ticket_data = ticket.get("ticket") or {}
        created_at = ticket.get("created_at", "")
        first_triage_at = ""
        triage_minutes = ""
        for log_entry in ensure_activity_log(ticket):
            action_type = (log_entry.get("action_type") or "").strip().lower()
            if "triage" in action_type:
                first_triage_at = log_entry.get("timestamp", "")
                break
        if created_at and first_triage_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                triage_dt = datetime.fromisoformat(first_triage_at.replace("Z", "+00:00"))
                triage_minutes = f"{max(0.0, (triage_dt - created_dt).total_seconds() / 60):.1f}"
            except ValueError:
                triage_minutes = ""
        export_rows.append(
            {
                "ticket_id": ticket.get("saved_id", ""),
                "title": clean_ticket_title(ticket_data.get("title")),
                "status": normalize_status(ticket.get("status")),
                "urgency": normalize_urgency(ticket_data.get("urgency")),
                "classification": ticket.get("classification", ""),
                "created_at": created_at,
                "first_triage_at": first_triage_at,
                "triage_minutes": triage_minutes,
            }
        )

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=[
            "ticket_id",
            "title",
            "status",
            "urgency",
            "classification",
            "created_at",
            "first_triage_at",
            "triage_minutes",
        ],
    )
    writer.writeheader()
    if export_rows:
        writer.writerows(export_rows)

    export_left, _ = st.columns([1, 4])
    with export_left:
        st.download_button(
            "Export CSV",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name=f"analytics_report_{start_date.isoformat()}_{end_date.isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )


if "open_tickets" not in st.session_state:
    st.session_state.open_tickets = load_tickets()
    for entry in st.session_state.open_tickets:
        entry["status"] = normalize_status(entry.get("status"))
        ensure_activity_log(entry)
if "closed_tickets" not in st.session_state:
    st.session_state.closed_tickets = load_closed_tickets()
    for entry in st.session_state.closed_tickets:
        entry["status"] = "completed"
        ensure_activity_log(entry)
if "deleted_tickets" not in st.session_state:
    st.session_state.deleted_tickets = load_deleted_tickets()
    for entry in st.session_state.deleted_tickets:
        entry["status"] = "deleted"
        ensure_activity_log(entry)
if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None
if "message_input" not in st.session_state:
    st.session_state.message_input = ""
if "active_queue" not in st.session_state:
    st.session_state.active_queue = "open"
if "queue_focus" not in st.session_state:
    st.session_state.queue_focus = st.session_state.active_queue
if "triage_feedback" not in st.session_state:
    st.session_state.triage_feedback = None
if "recent_viewed_ticket_ids" not in st.session_state:
    st.session_state.recent_viewed_ticket_ids = []
if "active_view" not in st.session_state:
    st.session_state.active_view = "Triage Workspace"
if "pending_view" not in st.session_state:
    st.session_state.pending_view = None

if st.session_state.pending_view is not None:
    st.session_state.active_view = st.session_state.pending_view
    st.session_state.pending_view = None

# Migration support: move completed tickets from open storage into archive storage.
migrated_open_tickets = []
migrated_closed_tickets = list(st.session_state.closed_tickets)
migrated_deleted_tickets = list(st.session_state.deleted_tickets)
for ticket in st.session_state.open_tickets:
    ensure_activity_log(ticket)
    if normalize_status(ticket.get("status")) == "completed":
        ticket["status"] = "completed"
        migrated_closed_tickets.append(ticket)
    elif normalize_status(ticket.get("status")) == "deleted":
        ticket["status"] = "deleted"
        migrated_deleted_tickets.append(ticket)
    else:
        ticket["status"] = normalize_status(ticket.get("status"))
        migrated_open_tickets.append(ticket)
st.session_state.open_tickets = migrated_open_tickets
st.session_state.closed_tickets = migrated_closed_tickets
st.session_state.deleted_tickets = migrated_deleted_tickets
for ticket in st.session_state.closed_tickets:
    ensure_activity_log(ticket)
for ticket in st.session_state.deleted_tickets:
    ensure_activity_log(ticket)
persist_ticket_state()

st.markdown(
    """
    <div class="hero-shell">
        <div class="app-title"><span>🩺</span><span>Healthcare Support Triage</span></div>
        <div class="app-subtitle">Three-panel workspace: queue on the left, overview/resolution in the middle, and new ticket search on the right. Demo mode is enabled, so tickets reset each session.</div>
        <div class="hero-metrics">
            <span class="hero-pill">Fast triage workflow</span>
            <span class="hero-pill">Priority-first queueing</span>
            <span class="hero-pill">Clean decision context</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

open_tickets = rank_tickets(list(st.session_state.open_tickets))
closed_tickets = rank_tickets(list(st.session_state.closed_tickets))
deleted_tickets = rank_tickets(list(st.session_state.deleted_tickets))
all_tickets = open_tickets + closed_tickets + deleted_tickets

view_options = ["Triage Workspace", "Ticket Desk", "Analytics Center"]
if st.session_state.active_view not in view_options:
    st.session_state.active_view = "Triage Workspace"

queue_options = ["open", "blocked", "archive", "deleted"]
if st.session_state.active_queue not in queue_options:
    st.session_state.active_queue = "open"
if st.session_state.get("queue_focus") != st.session_state.active_queue:
    st.session_state.queue_focus = st.session_state.active_queue
if "queue_sidebar_filter" not in st.session_state:
    st.session_state.queue_sidebar_filter = "all"


def render_queue_sidebar() -> None:
    blocked_tickets = [t for t in open_tickets if normalize_status(t.get("status")) == "blocked"]
    active_open_tickets = [t for t in open_tickets if normalize_status(t.get("status")) in {"new", "in_progress"}]
    spam_deleted_tickets = [t for t in deleted_tickets if (t.get("classification") or "").lower() == "spam"]
    non_spam_deleted_tickets = [t for t in deleted_tickets if (t.get("classification") or "").lower() != "spam"]

    queue_labels = {
        "open": f"Open ({len(active_open_tickets)})",
        "blocked": f"Blocked ({len(blocked_tickets)})",
        "archive": f"Archived ({len(closed_tickets)})",
        "deleted": f"Deleted ({len(deleted_tickets)})",
    }
    with st.sidebar:
        st.markdown("### Ticket queues")
        selected_queue = st.radio(
            "Queue focus",
            options=queue_options,
            format_func=lambda key: queue_labels[key],
            key="queue_focus",
            label_visibility="collapsed",
        )
        st.session_state.active_queue = selected_queue

        queue_map = {
            "open": ("🟢 Open queue", active_open_tickets),
            "blocked": ("⛔ Blocked queue", blocked_tickets),
            "archive": ("📦 Archived queue", closed_tickets),
            "deleted": ("🗑️ Deleted / spam", deleted_tickets),
        }
        queue_title, queue_tickets = queue_map[selected_queue]
        st.caption(queue_title)

        if selected_queue == "deleted":
            st.radio(
                "Deleted filter",
                options=["all", "deleted", "spam"],
                format_func=lambda value: {"all": "All", "deleted": "Deleted only", "spam": "Spam only"}[value],
                horizontal=True,
                key="queue_sidebar_filter",
                label_visibility="collapsed",
            )
            if st.session_state.queue_sidebar_filter == "spam":
                queue_tickets = spam_deleted_tickets
            elif st.session_state.queue_sidebar_filter == "deleted":
                queue_tickets = non_spam_deleted_tickets
        else:
            st.session_state.queue_sidebar_filter = "all"

        if not queue_tickets:
            st.caption("No tickets in this queue.")
            return

        st.markdown('<div class="queue-shell">', unsafe_allow_html=True)
        render_compact_queue_rows(selected_queue, queue_tickets[:9], "sidebar")
        st.markdown("</div>", unsafe_allow_html=True)


def render_main_queue_panel() -> None:
    blocked_tickets = [t for t in open_tickets if normalize_status(t.get("status")) == "blocked"]
    active_open_tickets = [t for t in open_tickets if normalize_status(t.get("status")) in {"new", "in_progress"}]
    queue_map = {
        "open": ("Open queue", active_open_tickets),
        "blocked": ("Blocked queue", blocked_tickets),
        "archive": ("Archived queue", closed_tickets),
        "deleted": ("Deleted / spam", deleted_tickets),
    }
    queue_title, queue_tickets = queue_map.get(st.session_state.active_queue, ("Open queue", active_open_tickets))
    st.markdown(f'<div class="queue-section-title-sm">{queue_title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="mini-note">Compact operational view for fast scanning and ticket selection.</div>', unsafe_allow_html=True)
    if not queue_tickets:
        st.caption("No tickets available in this queue.")
        return
    st.markdown('<div class="queue-shell">', unsafe_allow_html=True)
    render_compact_queue_rows(st.session_state.active_queue, queue_tickets[:10], "main_panel")
    st.markdown("</div>", unsafe_allow_html=True)


render_queue_sidebar()

st.radio(
    "Workspace view",
    options=view_options,
    horizontal=True,
    key="active_view",
    label_visibility="collapsed",
)

submitted = False
message = ""

if st.session_state.active_view == "Triage Workspace":
    st.markdown('<div class="three-col-header">🎯 Triage workspace</div>', unsafe_allow_html=True)
    st.caption("Use the collapsible sidebar to switch between Open, Blocked, Archived, and Deleted/Spam queues.")
    workspace_submitted, workspace_message = render_new_ticket_search_panel("triage_form_workspace")
    if workspace_submitted:
        submitted = True
        message = workspace_message

if st.session_state.active_view == "Ticket Desk":
    ticket_left, ticket_right = st.columns([1.75, 1.25], gap="large")
    with ticket_left:
        st.markdown('<div class="three-col-header">📋 Ticket details</div>', unsafe_allow_html=True)
        render_main_queue_panel()
        with st.container():
            st.markdown('<div class="scroll-panel">', unsafe_allow_html=True)
            render_selected_ticket_details(
                all_tickets,
                show_queue_move=False,
                show_activity_log=False,
            )
            st.markdown("</div>", unsafe_allow_html=True)
    with ticket_right:
        st.markdown('<div class="three-col-header">🧾 Activity Log</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="scroll-panel">', unsafe_allow_html=True)
            selected_ticket = get_selected_ticket(all_tickets)
            if selected_ticket:
                render_activity_log(selected_ticket, show_title=False)
            else:
                st.markdown('<div class="section-title">Activity Log</div>', unsafe_allow_html=True)
                st.caption("Select a ticket from Ticket Desk to view activity.")
            st.markdown("</div>", unsafe_allow_html=True)


if submitted:
    if not message.strip():
        st.session_state.triage_feedback = {"type": "warning", "message": "Please enter a message."}
        st.rerun()
    else:
        try:
            with st.spinner("Analyzing issue..."):
                result = asyncio.run(run_workflow(WorkflowInput(input_as_text=message.strip())))

            if result.get("ticket"):
                ticket_data = result["ticket"]
                ticket_data["urgency"] = normalize_urgency(ticket_data.get("urgency"))
                ticket_data["title"] = clean_ticket_title(ticket_data.get("title"))
            else:
                snippet = " ".join(message.strip().split())[:60]
                ticket_data = {
                    "ticketId": "",
                    "title": f"Spam: {snippet}" if snippet else "Spam message",
                    "urgency": "low",
                }

            normalized_ticket_id = ensure_unique_ticket_id(
                ticket_data.get("ticketId"),
                st.session_state.open_tickets
                + st.session_state.closed_tickets
                + st.session_state.deleted_tickets,
            )
            ticket_data["ticketId"] = normalized_ticket_id

            saved_entry = {
                "saved_id": normalized_ticket_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "deleted" if result["classification"] == "spam" else "new",
                "message": message.strip(),
                "classification": result["classification"],
                "ticket": ticket_data,
                "resolution": result["resolution"],
            }
            ensure_activity_log(saved_entry)
            append_activity_log(
                saved_entry,
                actor="ai",
                action_type="AI triage completed",
                details="Initial triage analysis and resolution draft generated.",
            )
            if result["classification"] == "spam":
                append_activity_log(
                    saved_entry,
                    actor="system",
                    action_type="Status changed",
                    details="Ticket classified as spam and moved to deleted queue.",
                )
            if result["classification"] == "spam":
                st.session_state.deleted_tickets.append(saved_entry)
                st.session_state.active_queue = "deleted"
            else:
                st.session_state.open_tickets.append(saved_entry)
                st.session_state.active_queue = "open"
            persist_ticket_state()
            st.session_state.selected_ticket_id = saved_entry["saved_id"]
            track_recent_ticket_view(saved_entry["saved_id"])
            st.session_state.pending_view = "Ticket Desk"
            st.session_state.triage_feedback = {
                "type": "success",
                "message": "Analysis complete. Ticket added to the queue.",
            }
            st.rerun()
        except Exception as e:
            st.session_state.triage_feedback = {"type": "error", "message": f"Error: {e}"}
            st.rerun()


if st.session_state.active_view == "Analytics Center":
    render_analytics_center(open_tickets, closed_tickets, deleted_tickets)
