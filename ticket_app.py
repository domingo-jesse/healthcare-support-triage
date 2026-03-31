import asyncio
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

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
            --bg-primary: #f5f7fb;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f8fafc;
            --text-primary: #1f2937;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
            --accent: #2f7df4;
            --accent-soft: #eaf2ff;
            --accent-danger: #ef4444;
            --card-gradient: linear-gradient(155deg, #ffffff 0%, #f7faff 100%);
            --overview-gradient: linear-gradient(155deg, #ffffff 0%, #eef5ff 100%);
            --resolution-gradient: linear-gradient(155deg, #ffffff 0%, #f2f8ff 100%);
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
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 100%;
            padding-left: 1.25rem;
            padding-right: 1.25rem;
        }
        .centered-stack {
            max-width: 900px;
            margin: 0 auto;
        }
        .three-col-header {
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 0.6rem;
        }
        .app-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
            color: var(--text-primary);
        }
        .app-subtitle {
            color: var(--text-muted);
            margin-bottom: 1.3rem;
        }
        .card {
            background: var(--card-gradient);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.95rem 1rem 0.8rem 1rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.75rem;
        }
        .card-overview {
            background: var(--overview-gradient);
        }
        .card-resolution {
            background: var(--resolution-gradient);
        }
        .card h3 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: var(--text-primary);
        }
        .metric-label {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 700;
        }
        .badge-low { background: #dbeafe; color: #1d4ed8; }
        .badge-medium { background: #fef3c7; color: #92400e; }
        .badge-high { background: #fee2e2; color: #b91c1c; }
        .badge-spam { background: #f3e8ff; color: #7e22ce; }
        .ticket-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-top: 0.35rem;
            margin-bottom: 0.5rem;
        }
        .section-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 0.7rem;
            margin-bottom: 0.35rem;
        }
        .response-box {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.7rem 0.8rem;
            white-space: pre-wrap;
            line-height: 1.45;
            color: var(--text-primary);
        }
        .overview-row-box {
            border: 0;
            border-radius: 0;
            background: transparent;
            padding: 0;
            margin-top: 0.4rem;
            box-shadow: none;
        }
        .overview-row-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.7rem;
            align-items: start;
        }
        .overview-row-item .section-label {
            margin-top: 0;
            margin-bottom: 0.2rem;
        }
        .overview-row-item .metric-value,
        .overview-row-item .ticket-title {
            margin: 0;
            font-size: 0.93rem;
        }
        .overview-submitted-request {
            margin-top: 0.5rem;
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 12px;
            border: 1px solid var(--border);
            background: var(--bg-secondary);
            color: var(--text-primary);
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
            border-radius: 10px;
            font-weight: 700;
            height: 2.5rem;
            background: #ffffff;
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
            height: auto;
            min-height: 4.2rem;
            text-align: left;
            padding: 0.7rem 0.75rem;
            transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
        }
        section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
            border-color: var(--accent);
            background: var(--accent-soft);
            box-shadow: 0 0 0 1px rgba(47, 125, 244, 0.15);
        }
        section[data-testid="stSidebar"] {
            min-width: 420px;
            max-width: 420px;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }
        .urgency-ticket-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.65rem 0.75rem;
            margin: 0.45rem 0 0.2rem 0;
            box-shadow: var(--shadow);
        }
        .urgency-ticket-card.high {
            background: rgba(239, 68, 68, 0.16);
            border-color: rgba(239, 68, 68, 0.35);
        }
        .urgency-ticket-card.medium {
            background: rgba(251, 191, 36, 0.16);
            border-color: rgba(251, 191, 36, 0.35);
        }
        .urgency-ticket-card.low {
            background: rgba(59, 130, 246, 0.14);
            border-color: rgba(59, 130, 246, 0.3);
        }
        .urgency-ticket-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.15rem;
        }
        .urgency-ticket-meta {
            font-size: 0.78rem;
            color: var(--text-primary);
            opacity: 0.9;
            line-height: 1.35;
        }
        div[data-testid="stFormSubmitButton"] > button {
            background: var(--accent-danger);
            border-color: var(--accent-danger);
            color: #fff;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .stat-box {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--bg-secondary);
            padding: 0.45rem 0.55rem;
            box-shadow: var(--shadow);
        }
        .stat-label { font-size: 0.74rem; color: var(--text-muted); }
        .stat-value { font-size: 1.08rem; color: var(--text-primary); font-weight: 800; line-height: 1.2; }
        .board-column {
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--bg-secondary);
            padding: 0.8rem;
            min-height: 250px;
        }
        .board-title {
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 0.4rem;
        }
        .column-chip {
            display: inline-block;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            padding: 0.15rem 0.5rem;
            font-size: 0.72rem;
            margin-left: 0.45rem;
            font-weight: 700;
        }
        .ticket-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--card-gradient);
            padding: 0.65rem 0.75rem;
            margin: 0.45rem 0;
        }
        .ticket-meta {
            color: var(--text-muted);
            font-size: 0.76rem;
            margin-top: 0.2rem;
        }
        .mini-note {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.2rem;
            margin-bottom: 0.45rem;
        }
        .queue-item-row {
            margin: 0.35rem 0;
        }
        .queue-scroll-wrap {
            max-height: 72vh;
            overflow-y: auto;
            padding-right: 0.25rem;
        }
        .queue-urgency-box {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.45rem 0.55rem;
            line-height: 1.2;
            background: rgba(15, 23, 42, 0.02);
        }
        .queue-urgency-box.high {
            background: rgba(239, 68, 68, 0.14);
            border-color: rgba(239, 68, 68, 0.3);
        }
        .queue-urgency-box.medium {
            background: rgba(251, 191, 36, 0.14);
            border-color: rgba(251, 191, 36, 0.3);
        }
        .queue-urgency-box.low {
            background: rgba(59, 130, 246, 0.12);
            border-color: rgba(59, 130, 246, 0.28);
        }
        .queue-urgency-title {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.12rem;
        }
        .queue-urgency-meta {
            font-size: 0.72rem;
            color: var(--text-muted);
        }
        .queue-ticket-button div[data-testid="stButton"] > button {
            border-radius: 10px;
            border: 1px solid var(--border);
            min-height: 58px;
            padding: 0.45rem 0.55rem;
            text-align: left;
            font-size: 0.8rem;
            background: rgba(15, 23, 42, 0.05);
        }
        .queue-ticket-button.high div[data-testid="stButton"] > button {
            background: rgba(239, 68, 68, 0.18);
            border-color: rgba(239, 68, 68, 0.35);
        }
        .queue-ticket-button.medium div[data-testid="stButton"] > button {
            background: rgba(251, 191, 36, 0.18);
            border-color: rgba(245, 158, 11, 0.35);
        }
        .queue-ticket-button.low div[data-testid="stButton"] > button {
            background: rgba(59, 130, 246, 0.16);
            border-color: rgba(59, 130, 246, 0.33);
        }
        .queue-ticket-button div[data-testid="stButton"] > button:hover {
            filter: brightness(0.98);
            border-color: var(--accent);
        }
        .queue-table {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--bg-secondary);
            overflow: hidden;
            box-shadow: var(--shadow);
        }
        .queue-title {
            background: #f9fafb;
            border-bottom: 1px solid var(--border);
            padding: 0.9rem 1rem;
            font-weight: 800;
            font-size: 1rem;
        }
        .queue-head {
            display: grid;
            grid-template-columns: 72px 120px 2fr 190px 165px 130px 120px;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            background: #f9fafb;
            border-bottom: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .queue-row {
            display: grid;
            grid-template-columns: 72px 120px 2fr 190px 165px 130px 120px;
            gap: 0.5rem;
            align-items: center;
            padding: 0.7rem 1rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.92rem;
        }
        .queue-row:last-child {
            border-bottom: 0;
        }
        .ticket-type {
            font-weight: 600;
        }
        .ticket-urgency {
            color: var(--text-primary);
        }
        .ticket-date {
            color: var(--text-muted);
            font-size: 0.84rem;
        }
        .ticket-assignee {
            color: var(--text-primary);
            font-weight: 600;
        }
        .ticket-id-link {
            color: var(--accent);
            font-weight: 700;
            text-decoration: none;
        }
        .ticket-id-link:hover {
            text-decoration: underline;
        }
        @media (max-width: 1200px) {
            .queue-head, .queue-row {
                grid-template-columns: 62px 100px 1.7fr 160px 150px 110px 110px;
                font-size: 0.82rem;
            }
            .overview-row-grid {
                grid-template-columns: 1fr 1fr;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

TICKETS_DB_PATH = Path(__file__).parent / "tickets_store.json"
URGENCY_RANK = {"high": 0, "medium": 1, "low": 2}
STATUS_STAGES = ("new", "in_progress", "blocked", "completed")
STATUS_LABELS = {
    "new": "New",
    "in_progress": "In Progress",
    "blocked": "Blocked",
    "completed": "Completed",
}
PROGRESS_OPTIONS = ("in_progress", "blocked", "completed")
OPEN_STATUSES = ("new", "in_progress", "blocked")


def load_tickets() -> list[dict]:
    if not TICKETS_DB_PATH.exists():
        return []
    try:
        data = json.loads(TICKETS_DB_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
    except (json.JSONDecodeError, OSError):
        return []
    return []


def save_tickets(tickets: list[dict]) -> None:
    temp_path = TICKETS_DB_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    temp_path.replace(TICKETS_DB_PATH)


def rank_tickets(tickets: list[dict]) -> list[dict]:
    return sorted(
        tickets,
        key=lambda t: (
            URGENCY_RANK.get((t.get("ticket") or {}).get("urgency", "medium").lower(), 1),
            STATUS_STAGES.index(normalize_status(t.get("status"))),
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
    if normalized in {"closed", "done"}:
        return "completed"
    return normalized if normalized in STATUS_STAGES else "new"


def ensure_unique_ticket_id(ticket_id: str | None, existing_tickets: list[dict]) -> str:
    candidate = (ticket_id or "").strip()
    existing_ids = {entry.get("saved_id") for entry in existing_tickets}

    if not candidate:
        candidate = f"TKT-{uuid4().hex[:8].upper()}"

    if candidate in existing_ids:
        candidate = f"{candidate}-{uuid4().hex[:4].upper()}"

    return candidate


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
    key_prefix: str = "overview",
) -> tuple[str, str]:
    ticket = result.get("ticket") or {}
    st.markdown('<div class="overview-row-box"><div class="overview-row-grid">', unsafe_allow_html=True)
    col_classification, col_ticket_id, col_title, col_urgency, col_status = st.columns(5)
    with col_classification:
        st.markdown('<div class="section-label">Classification</div>', unsafe_allow_html=True)
        st.markdown(
            classification_badge_html(result.get("classification", "ticket")),
            unsafe_allow_html=True,
        )
    with col_ticket_id:
        st.markdown('<div class="section-label">Ticket ID</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{html.escape(ticket.get("ticketId", "N/A"))}</div>',
            unsafe_allow_html=True,
        )
    with col_title:
        st.markdown('<div class="section-label">Title</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ticket-title">{html.escape(ticket.get("title", "Untitled ticket"))}</div>',
            unsafe_allow_html=True,
        )
    with col_urgency:
        st.markdown('<div class="section-label">Urgency</div>', unsafe_allow_html=True)
        urgency_options = ["low", "medium", "high"]
        selected_urgency = st.selectbox(
            "Urgency",
            options=urgency_options,
            index=urgency_options.index(default_urgency),
            format_func=lambda urgency: urgency.title(),
            key=f"{key_prefix}_urgency_{ticket.get('ticketId', 'unknown')}",
            label_visibility="collapsed",
        )
    with col_status:
        st.markdown('<div class="section-label">Status</div>', unsafe_allow_html=True)
        selected_status = st.selectbox(
            "Status",
            options=list(PROGRESS_OPTIONS),
            index=list(PROGRESS_OPTIONS).index(default_status),
            format_func=lambda status: STATUS_LABELS[status],
            key=f"{key_prefix}_status_{ticket.get('ticketId', 'unknown')}",
            label_visibility="collapsed",
        )
    st.markdown("</div></div>", unsafe_allow_html=True)
    if submitted_request:
        st.markdown(
            '<div class="overview-submitted-request"><div class="section-label">Submitted Request</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="response-box">{html.escape(submitted_request)}</div>',
            unsafe_allow_html=True,
        )

    root_cause, next_steps, suggested_response = parse_resolution_text(result["resolution"])

    st.markdown('<div class="card card-resolution"><h3>🧠 Resolution</h3>', unsafe_allow_html=True)

    if root_cause:
        st.markdown('<div class="section-label">Likely Root Cause</div>', unsafe_allow_html=True)
        st.write(root_cause)

    if next_steps:
        st.markdown(
            '<div class="section-label">Recommended Next Steps</div>', unsafe_allow_html=True
        )
        st.write(next_steps)
    else:
        st.markdown('<div class="section-label">Resolution Notes</div>', unsafe_allow_html=True)
        st.write(result["resolution"])

    if suggested_response:
        st.markdown(
            '<div class="section-label">Suggested Customer Response</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="response-box">{html.escape(suggested_response)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    return selected_urgency, selected_status


def render_empty_result_placeholder() -> None:
    st.markdown('<div class="card card-resolution"><h3>🧠 Resolution</h3>', unsafe_allow_html=True)
    st.caption("Resolution output will appear here.")
    st.markdown(
        '<div class="mini-note">Choose a ticket from the queue or run a new triage search to populate this panel.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


if "tickets" not in st.session_state:
    st.session_state.tickets = load_tickets()
    for entry in st.session_state.tickets:
        entry["status"] = normalize_status(entry.get("status"))
if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None
if "message_input" not in st.session_state:
    st.session_state.message_input = ""

st.markdown('<div class="app-title">🩺 Healthcare Support Triage</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Three-panel workspace: queue on the left, overview/resolution in the middle, and new ticket search on the right.</div>',
    unsafe_allow_html=True,
)

all_tickets = list(st.session_state.tickets)
for ticket in all_tickets:
    ticket["status"] = normalize_status(ticket.get("status"))
filtered_tickets = rank_tickets(all_tickets)
open_tickets = [ticket for ticket in filtered_tickets if normalize_status(ticket.get("status")) in OPEN_STATUSES]
closed_tickets = [ticket for ticket in filtered_tickets if normalize_status(ticket.get("status")) == "completed"]

status_counts = {status: 0 for status in STATUS_STAGES}
for ticket in filtered_tickets:
    status_counts[normalize_status(ticket.get("status"))] += 1

left_col, middle_col, right_col = st.columns([1.2, 1.25, 1.55], gap="large")

with left_col:
    st.markdown('<div class="three-col-header">📊 Queue stats</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="stats-grid" style="grid-template-columns: 1fr; margin-bottom: 0.5rem;">
          <div class="stat-box"><div class="stat-label">Total Tickets</div><div class="stat-value">{len(filtered_tickets)}</div></div>
          <div class="stat-box"><div class="stat-label">Open Queue</div><div class="stat-value">{len(open_tickets)}</div></div>
          <div class="stat-box"><div class="stat-label">Completed/Closed</div><div class="stat-value">{len(closed_tickets)}</div></div>
          <div class="stat-box"><div class="stat-label">High Urgency</div><div class="stat-value">{sum(1 for t in filtered_tickets if normalize_urgency((t.get('ticket') or {}).get('urgency')) == 'high')}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="three-col-header">🎫 Queues</div>', unsafe_allow_html=True)
    st.caption(f"{len(filtered_tickets)} total ticket(s)")

    if not filtered_tickets:
        st.caption("No tickets match the current queue.")

    urgency_icons = {"high": "🟥", "medium": "🟨", "low": "🟦"}
    urgency_labels = {"high": "High urgency", "medium": "Medium urgency", "low": "Low urgency"}

    def render_queue_section(section_key: str, section_title: str, tickets: list[dict]) -> None:
        st.markdown(f"#### {section_title} ({len(tickets)})")
        if not tickets:
            st.caption("No tickets in this queue.")
            return

        tickets_by_urgency: dict[str, list[dict]] = {"high": [], "medium": [], "low": []}
        for ticket in tickets:
            urgency = normalize_urgency((ticket.get("ticket") or {}).get("urgency"))
            tickets_by_urgency[urgency].append(ticket)

        for urgency in ("high", "medium", "low"):
            urgency_tickets = tickets_by_urgency[urgency]
            if not urgency_tickets:
                continue

            with st.expander(
                f"{urgency_icons[urgency]} {urgency_labels[urgency]} ({len(urgency_tickets)})",
                expanded=True,
            ):
                for ticket in urgency_tickets:
                    ticket_id = ticket.get("saved_id", "")
                    title = (ticket.get("ticket") or {}).get("title", "Untitled ticket")
                    queue_title = f"{urgency_icons[urgency]} {title}"
                    st.markdown(
                        f'<div class="queue-item-row queue-ticket-button {urgency}">',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        queue_title,
                        key=f"queue_{section_key}_{ticket_id}",
                        use_container_width=True,
                        help=f"Open ticket #{ticket_id[-6:] if ticket_id else 'N/A'}",
                    ):
                        st.session_state.selected_ticket_id = ticket_id
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    with st.container(height=640, border=False):
        render_queue_section("open", "🟢 Open Queue", open_tickets)
        st.markdown("---")
        render_queue_section("closed", "✅ Completed/Closed Queue", closed_tickets)

with middle_col:
    st.markdown('<div class="three-col-header">📋 Ticket details</div>', unsafe_allow_html=True)
    if st.session_state.selected_ticket_id:
        selected = next(
            (
                entry
                for entry in st.session_state.tickets
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

            urgency_choice, progress_choice = render_result(
                {
                    "classification": selected.get("classification", "ticket"),
                    "ticket": selected_ticket,
                    "resolution": selected.get("resolution", ""),
                },
                submitted_request=selected.get("message", ""),
                default_urgency=default_urgency,
                default_status=default_status,
                key_prefix=f"selected_{selected.get('saved_id')}",
            )

            if urgency_choice != current_urgency or progress_choice != current_status:
                selected_ticket["urgency"] = urgency_choice
                selected["status"] = progress_choice
                save_tickets(st.session_state.tickets)
                st.rerun()
        else:
            render_empty_result_placeholder()
    else:
        render_empty_result_placeholder()

with right_col:
    st.markdown('<div class="three-col-header">🔎 New ticket search</div>', unsafe_allow_html=True)
    with st.form("triage_form", clear_on_submit=True):
        message = st.text_area(
            "Incoming support message",
            key="message_input",
            height=250,
            placeholder="Paste a support ticket here...",
        )
        submitted = st.form_submit_button("Run triage", type="primary", use_container_width=True)


if submitted:
    if not message.strip():
        st.warning("Please enter a message.")
    else:
        try:
            with st.spinner("Analyzing issue..."):
                result = asyncio.run(run_workflow(WorkflowInput(input_as_text=message.strip())))

            if result.get("ticket"):
                ticket_data = result["ticket"]
                ticket_data["urgency"] = normalize_urgency(ticket_data.get("urgency"))
                ticket_data["title"] = (ticket_data.get("title") or "Untitled ticket").strip()
            else:
                snippet = " ".join(message.strip().split())[:60]
                ticket_data = {
                    "ticketId": "",
                    "title": f"Spam: {snippet}" if snippet else "Spam message",
                    "urgency": "low",
                }

            normalized_ticket_id = ensure_unique_ticket_id(
                ticket_data.get("ticketId"), st.session_state.tickets
            )
            ticket_data["ticketId"] = normalized_ticket_id

            saved_entry = {
                "saved_id": normalized_ticket_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "new",
                "message": message.strip(),
                "classification": result["classification"],
                "ticket": ticket_data,
                "resolution": result["resolution"],
            }
            st.session_state.tickets.append(saved_entry)
            save_tickets(st.session_state.tickets)
            st.session_state.selected_ticket_id = saved_entry["saved_id"]

            st.success("Analysis complete")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
