import asyncio
import html
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
            max-width: 1480px;
            margin: 0 auto;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
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
        .queue-item-row {
            margin: 0.15rem 0;
            border-radius: 10px;
        }
        .queue-ticket-button div[data-testid="stButton"] > button {
            border-radius: 10px;
            border: 1px solid var(--ticket-border, transparent);
            min-height: 50px;
            padding: 0.55rem 0.65rem;
            text-align: left;
            font-size: 0.86rem;
            font-weight: 600;
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
        "title": "Missing Provider Fax Number",
        "description": (
            "User is submitting a prior auth but the provider fax number is not populating "
            "automatically. Requesting help to locate or enter correct fax number."
        ),
        "impact": "Minor delay in submission",
        "urgency": "low",
    },
    {
        "title": "Duplicate Prior Auth Entry",
        "description": (
            "User accidentally created two prior auth requests for the same patient and "
            "procedure. Needs guidance on which one to cancel."
        ),
        "impact": "No immediate patient impact",
        "urgency": "low",
    },
    {
        "title": "Unable to Attach Clinical Documents",
        "description": (
            "User cannot upload required clinical notes when submitting prior auth. "
            "Upload button is not responding."
        ),
        "impact": "Delays authorization review",
        "urgency": "medium",
    },
    {
        "title": "Incorrect CPT Code Suggestion",
        "description": (
            "System is suggesting the wrong CPT code for a procedure. User wants to "
            "confirm correct coding before submission."
        ),
        "impact": "Risk of denial if submitted incorrectly",
        "urgency": "medium",
    },
    {
        "title": "Prior Auth Submission Failing",
        "description": (
            'User receives error when trying to submit prior auth. Error message says '
            '"submission failed – retry later." Issue persists after multiple attempts.'
        ),
        "impact": "Patient care delayed",
        "urgency": "high",
    },
    {
        "title": "Authorization Status Not Updating",
        "description": (
            "Prior auth was approved by payer, but system still shows pending status. "
            "User needs update to proceed with treatment scheduling."
        ),
        "impact": "Blocking patient treatment",
        "urgency": "high",
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
                "status": "new",
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


def render_analytics_center(open_tickets: list[dict], closed_tickets: list[dict], deleted_tickets: list[dict]) -> None:
    st.markdown('<div class="three-col-header">📊 Analytics center</div>', unsafe_allow_html=True)

    total_tickets = len(open_tickets) + len(closed_tickets) + len(deleted_tickets)
    active_tickets = len([t for t in open_tickets if normalize_status(t.get("status")) in {"new", "in_progress"}])
    blocked_tickets = len([t for t in open_tickets if normalize_status(t.get("status")) == "blocked"])
    archived_tickets = len(closed_tickets)
    spam_tickets = len([t for t in deleted_tickets if (t.get("classification") or "").lower() == "spam"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total tickets", total_tickets)
    c2.metric("Active", active_tickets)
    c3.metric("Blocked", blocked_tickets)
    c4.metric("Archived", archived_tickets)
    c5.metric("Spam", spam_tickets)

    urgency_totals = {"high": 0, "medium": 0, "low": 0}
    for ticket in open_tickets + closed_tickets:
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
    all_ticket_map = {
        ticket.get("saved_id"): ticket for ticket in (open_tickets + closed_tickets + deleted_tickets)
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
    left_col, right_col = st.columns([1.35, 1.1], gap="large")

    with left_col:
        st.markdown('<div class="three-col-header">🎫 Ticket queues</div>', unsafe_allow_html=True)
        blocked_tickets = [t for t in open_tickets if normalize_status(t.get("status")) == "blocked"]
        active_open_tickets = [t for t in open_tickets if normalize_status(t.get("status")) in {"new", "in_progress"}]

        def move_ticket_to_queue(ticket: dict, target_queue: str) -> None:
            ticket_id = ticket.get("saved_id")
            if not ticket_id:
                return

            open_match = next((t for t in st.session_state.open_tickets if t.get("saved_id") == ticket_id), None)
            closed_match = next((t for t in st.session_state.closed_tickets if t.get("saved_id") == ticket_id), None)
            deleted_match = next((t for t in st.session_state.deleted_tickets if t.get("saved_id") == ticket_id), None)
            active_ticket = open_match or closed_match or deleted_match or ticket

            st.session_state.open_tickets = [t for t in st.session_state.open_tickets if t.get("saved_id") != ticket_id]
            st.session_state.closed_tickets = [t for t in st.session_state.closed_tickets if t.get("saved_id") != ticket_id]
            st.session_state.deleted_tickets = [t for t in st.session_state.deleted_tickets if t.get("saved_id") != ticket_id]

            previous_status = normalize_status(active_ticket.get("status"))
            if target_queue == "open":
                active_ticket["status"] = "in_progress"
                st.session_state.open_tickets.append(active_ticket)
            elif target_queue == "blocked":
                active_ticket["status"] = "blocked"
                st.session_state.open_tickets.append(active_ticket)
            elif target_queue == "archived":
                active_ticket["status"] = "completed"
                st.session_state.closed_tickets.append(active_ticket)
            elif target_queue == "deleted":
                active_ticket["status"] = "deleted"
                st.session_state.deleted_tickets.append(active_ticket)

            new_status = normalize_status(active_ticket.get("status"))
            if new_status != previous_status:
                append_activity_log(
                    active_ticket,
                    actor="human_agent",
                    action_type="Status changed",
                    details=f"Status updated from {previous_status} to {new_status}.",
                )
            st.session_state.active_queue = "archive" if target_queue == "archived" else target_queue
            persist_ticket_state()

        def ticket_queue_label(ticket: dict, section_key: str) -> str:
            if section_key.startswith("open_"):
                return "Open Queue"
            if section_key.startswith("blocked_"):
                return "Blocked Queue"
            if section_key == "archive":
                return "Archived Queue"
            if section_key.startswith("deleted"):
                return "Deleted / Spam"
            status = normalize_status(ticket.get("status"))
            if status in {"new", "in_progress"}:
                return "Open Queue"
            if status == "blocked":
                return "Blocked Queue"
            if status == "completed":
                return "Archived Queue"
            return "Deleted / Spam"

        def render_ticket_buttons(section_key: str, tickets: list[dict]) -> None:
            if not tickets:
                st.caption("No tickets in this section.")
                return
            for idx, ticket in enumerate(tickets):
                ticket_id = ticket.get("saved_id", "")
                widget_suffix = f"{ticket_id or 'noid'}_{idx}"
                title = clean_ticket_title((ticket.get("ticket") or {}).get("title"))
                is_selected = st.session_state.selected_ticket_id == ticket_id
                widget_key = f"queue_{section_key}_{widget_suffix}"
                urgency = normalize_urgency((ticket.get("ticket") or {}).get("urgency"))
                urgency_styles = {
                    "high": {
                        "accent": "#dc2626",
                        "border": "#e2e8f0",
                        "bg": "#ffffff",
                        "text": "#0f172a",
                        "selected_border": "#cbd5e1",
                        "selected_shadow": "rgba(148, 163, 184, 0.25)",
                        "selected_bg": "#f8fafc",
                    },
                    "medium": {
                        "accent": "#f59e0b",
                        "border": "#e2e8f0",
                        "bg": "#ffffff",
                        "text": "#0f172a",
                        "selected_border": "#cbd5e1",
                        "selected_shadow": "rgba(148, 163, 184, 0.25)",
                        "selected_bg": "#f8fafc",
                    },
                    "low": {
                        "accent": "#22c55e",
                        "border": "#e2e8f0",
                        "bg": "#ffffff",
                        "text": "#0f172a",
                        "selected_border": "#cbd5e1",
                        "selected_shadow": "rgba(148, 163, 184, 0.25)",
                        "selected_bg": "#f8fafc",
                    },
                }
                button_style = urgency_styles.get(urgency, urgency_styles["medium"])
                urgency_label = urgency.title()
                selection_css = ""
                if is_selected:
                    selection_css = f"""
                    .st-key-{widget_key} button {{
                        border-color: {button_style["selected_border"]} !important;
                        box-shadow: inset 0 0 0 1px {button_style["selected_shadow"]} !important;
                        background: {button_style["selected_bg"]} !important;
                    }}
                    """
                st.markdown(
                    f"""
                    <style>
                    .st-key-{widget_key} button {{
                        border-radius: 10px;
                        border: 1px solid {button_style["border"]} !important;
                        box-shadow: inset 4px 0 0 {button_style["accent"]};
                        min-height: 50px;
                        padding: 0.55rem 0.65rem;
                        text-align: left;
                        font-size: 0.86rem;
                        font-weight: 600;
                        transition: all 120ms ease-in-out;
                        background: {button_style["bg"]} !important;
                        color: {button_style["text"]} !important;
                        white-space: normal;
                    }}
                    .st-key-{widget_key} button:hover {{
                        transform: translateY(-1px);
                        filter: brightness(0.96);
                    }}
                    {selection_css}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"● {title}   [{urgency_label}]",
                    key=widget_key,
                    use_container_width=True,
                    help=f"Open ticket #{ticket_id[-6:] if ticket_id else 'N/A'}",
                ):
                    st.session_state.selected_ticket_id = ticket_id
                    track_recent_ticket_view(ticket_id)
                    st.session_state.active_queue = section_key
                    st.session_state.pending_view = "Ticket Desk"
                    st.rerun()

        queue_sections = [
            ("🟢 Open Queue", "Ranked by urgency", "open", active_open_tickets),
            ("⛔ Blocked Queue", "Tickets needing unblocking", "blocked", blocked_tickets),
            ("📦 Archived Queue", "Completed tickets", "archive", closed_tickets),
            ("🗑️ Deleted / Spam", "Deleted and spam tickets", "deleted", deleted_tickets),
        ]
        queue_labels = {
            "open": f"Open ({len(active_open_tickets)})",
            "blocked": f"Blocked ({len(blocked_tickets)})",
            "archive": f"Archived ({len(closed_tickets)})",
            "deleted": f"Deleted ({len(deleted_tickets)})",
        }
        queue_options = ["open", "blocked", "archive", "deleted"]
        if st.session_state.active_queue not in queue_options:
            st.session_state.active_queue = "open"
        if st.session_state.queue_focus not in queue_options:
            st.session_state.queue_focus = st.session_state.active_queue
        if st.session_state.queue_focus != st.session_state.active_queue:
            st.session_state.queue_focus = st.session_state.active_queue
        st.radio(
            "Queue focus",
            options=queue_options,
            format_func=lambda key: queue_labels[key],
            horizontal=True,
            key="queue_focus",
            label_visibility="collapsed",
        )
        st.session_state.active_queue = st.session_state.queue_focus
        selected_section = next(
            (section for section in queue_sections if section[2] == st.session_state.active_queue),
            queue_sections[0],
        )
        with st.container():
            st.markdown('<div class="scroll-panel">', unsafe_allow_html=True)
            queue_name, _queue_caption, queue_key, queue_tickets = selected_section
            st.markdown(
                f'<div class="queue-section-title-lg">{queue_name}</div>',
                unsafe_allow_html=True,
            )
            render_ticket_buttons(queue_key, queue_tickets)
            st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        workspace_submitted, workspace_message = render_new_ticket_search_panel("triage_form_workspace")
        if workspace_submitted:
            submitted = True
            message = workspace_message

if st.session_state.active_view == "Ticket Desk":
    ticket_left, ticket_right = st.columns([1.75, 1.25], gap="large")
    with ticket_left:
        st.markdown('<div class="three-col-header">📋 Ticket details</div>', unsafe_allow_html=True)
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
