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
            --card-gradient: linear-gradient(180deg, #ffffff 0%, #ffffff 100%);
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
            padding: 1.25rem 1.25rem 1rem 1.25rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
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
            margin-top: 1rem;
            margin-bottom: 0.35rem;
        }
        .response-box {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 1rem;
            white-space: pre-wrap;
            line-height: 1.55;
            color: var(--text-primary);
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
        div[data-testid="stFormSubmitButton"] > button {
            background: var(--accent-danger);
            border-color: var(--accent-danger);
            color: #fff;
        }
        .toolbar-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--bg-secondary);
            padding: 0.75rem 1rem;
            margin: 0.4rem 0 0.95rem 0;
            box-shadow: var(--shadow);
            color: var(--text-primary);
            font-weight: 700;
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
            padding: 0.8rem;
            box-shadow: var(--shadow);
        }
        .stat-label { font-size: 0.8rem; color: var(--text-muted); }
        .stat-value { font-size: 1.3rem; color: var(--text-primary); font-weight: 800; }
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
            margin-top: 0.3rem;
            margin-bottom: 0.65rem;
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
        }
    </style>
    """,
    unsafe_allow_html=True,
)

EXAMPLES = {
    "Profile update issue": """Hi,

I tried updating my phone number and office location in my profile settings, but it doesn’t seem to save after I click "Update."

It’s not urgent, but I wanted to report it in case something is broken.

Thanks,
Mark""",
    "Authorization outage": """A few of my coworkers are having the same issue. We cannot submit or check prior authorizations right now and it is blocking our work.""",
    "Spam": """Buy cheap insurance leads now and click this link for an amazing deal.""",
}

TICKETS_DB_PATH = Path(__file__).parent / "tickets_store.json"
URGENCY_RANK = {"high": 0, "medium": 1, "low": 2}
URGENCY_SCORES = {"high": 100, "medium": 60, "low": 30}
STATUS_STAGES = ("new", "in_progress", "blocked", "completed")
STATUS_LABELS = {
    "new": "New",
    "in_progress": "In Progress",
    "blocked": "Blocked",
    "completed": "Completed",
}


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


def render_result(result: dict, submitted_request: str = "") -> None:
    left, right = st.columns([1, 1.2], gap="large")

    with left:
        st.markdown('<div class="card"><h3>📌 Overview</h3>', unsafe_allow_html=True)
        if submitted_request:
            st.markdown('<div class="section-label">Submitted Request</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="response-box">{html.escape(submitted_request)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="metric-label">Classification</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-value">{result["classification"].upper()}</div>',
            unsafe_allow_html=True,
        )

        if result["ticket"]:
            ticket = result["ticket"]

            st.markdown('<div class="section-label">Ticket ID</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="metric-value">{ticket["ticketId"]}</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="section-label">Title</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="ticket-title">{ticket["title"]}</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="section-label">Urgency</div>', unsafe_allow_html=True)
            st.markdown(urgency_badge_html(ticket["urgency"]), unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        root_cause, next_steps, suggested_response = parse_resolution_text(result["resolution"])

        st.markdown('<div class="card"><h3>🧠 Resolution</h3>', unsafe_allow_html=True)

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
                f'<div class="response-box">{suggested_response}</div>',
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
    '<div class="app-subtitle">Simple triage queue with a clean service-desk layout, search, and status tracking.</div>',
    unsafe_allow_html=True,
)
with st.expander("Examples", expanded=False):
    example_choice = st.selectbox("Load a sample", ["Custom"] + list(EXAMPLES.keys()))
    st.caption("Use one of these sample issues or paste your own message.")
    if example_choice != "Custom":
        st.session_state.message_input = EXAMPLES[example_choice]

with st.form("triage_form", clear_on_submit=True):
    message = st.text_area(
        "Incoming support message",
        key="message_input",
        height=190,
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
                result["ticket"]["urgency"] = normalize_urgency(result["ticket"].get("urgency"))
                normalized_ticket_id = ensure_unique_ticket_id(
                    result["ticket"].get("ticketId"), st.session_state.tickets
                )
                result["ticket"]["ticketId"] = normalized_ticket_id

                saved_entry = {
                    "saved_id": normalized_ticket_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "new",
                    "message": message.strip(),
                    "classification": result["classification"],
                    "ticket": result["ticket"],
                    "resolution": result["resolution"],
                }
                st.session_state.tickets.append(saved_entry)
                save_tickets(st.session_state.tickets)
                st.session_state.selected_ticket_id = saved_entry["saved_id"]

            st.success("Analysis complete")
            render_result(result, submitted_request=message.strip())
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown('<div class="toolbar-card">🎛️ Ticket board controls</div>', unsafe_allow_html=True)
controls_left, controls_mid, controls_right = st.columns([1.2, 1, 1.1], gap="medium")
with controls_left:
    search_term = st.text_input("Search tickets", placeholder="Search by title or message")
with controls_mid:
    urgency_filter = st.selectbox("Filter by urgency", ["All", "high", "medium", "low"])
with controls_right:
    sort_mode = st.selectbox(
        "Sort tickets",
        ["Urgency (high to low)", "Newest first", "Oldest first"],
    )

all_tickets = list(st.session_state.tickets)
for ticket in all_tickets:
    ticket["status"] = normalize_status(ticket.get("status"))


def ticket_matches(ticket: dict) -> bool:
    title = ((ticket.get("ticket") or {}).get("title") or "").lower()
    body = (ticket.get("message") or "").lower()
    urgency = normalize_urgency((ticket.get("ticket") or {}).get("urgency"))
    term_ok = not search_term.strip() or search_term.lower().strip() in f"{title} {body}"
    urgency_ok = urgency_filter == "All" or urgency == urgency_filter
    return term_ok and urgency_ok


filtered_tickets = [t for t in all_tickets if ticket_matches(t)]
if sort_mode == "Urgency (high to low)":
    filtered_tickets = sorted(
        filtered_tickets,
        key=lambda t: URGENCY_SCORES.get(normalize_urgency((t.get("ticket") or {}).get("urgency")), 0),
        reverse=True,
    )
elif sort_mode == "Newest first":
    filtered_tickets = sorted(filtered_tickets, key=lambda t: t.get("created_at", ""), reverse=True)
elif sort_mode == "Oldest first":
    filtered_tickets = sorted(filtered_tickets, key=lambda t: t.get("created_at", ""))

status_counts = {status: 0 for status in STATUS_STAGES}
for ticket in filtered_tickets:
    status_counts[normalize_status(ticket.get("status"))] += 1

st.markdown(
    f"""
    <div class="stats-grid">
      <div class="stat-box"><div class="stat-label">Total Tickets</div><div class="stat-value">{len(filtered_tickets)}</div></div>
      <div class="stat-box"><div class="stat-label">High Urgency</div><div class="stat-value">{sum(1 for t in filtered_tickets if normalize_urgency((t.get("ticket") or {}).get("urgency")) == "high")}</div></div>
      <div class="stat-box"><div class="stat-label">In Progress</div><div class="stat-value">{status_counts['in_progress']}</div></div>
      <div class="stat-box"><div class="stat-label">Blocked</div><div class="stat-value">{status_counts['blocked']}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="mini-note">Queue view replaces kanban movement controls for easier triage updates.</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown("## 🎫 Ticket Queue")
st.sidebar.caption(f"{len(filtered_tickets)} ticket(s)")

if not filtered_tickets:
    st.sidebar.caption("No tickets match the current filters.")

for ticket in filtered_tickets:
    ticket_id = ticket.get("saved_id", "")
    urgency = normalize_urgency((ticket.get("ticket") or {}).get("urgency"))
    title = (ticket.get("ticket") or {}).get("title", "Untitled ticket")
    created_display = (ticket.get("created_at") or "").replace("T", " ").split(".")[0][:16] or "N/A"
    ticket_status = normalize_status(ticket.get("status"))
    queue_label = (
        f"#{ticket_id[-6:] if ticket_id else 'N/A'} · {title}\n"
        f"{urgency.upper()} · {STATUS_LABELS[ticket_status]} · {created_display}"
    )
    if st.sidebar.button(
        queue_label,
        key=f"queue_open_{ticket_id}",
        use_container_width=True,
        help="Open this ticket to view submitted request and suggested response.",
    ):
        st.session_state.selected_ticket_id = ticket_id
        st.rerun()

if st.session_state.selected_ticket_id:
    selected_ticket = next(
        (entry for entry in st.session_state.tickets if entry.get("saved_id") == st.session_state.selected_ticket_id),
        None,
    )
    if selected_ticket:
        selected_urgency = normalize_urgency((selected_ticket.get("ticket") or {}).get("urgency"))
        selected_status = normalize_status(selected_ticket.get("status"))
        st.markdown("### Selected ticket controls")
        ctrl_cols = st.columns([1, 1], gap="medium")
        with ctrl_cols[0]:
            urgency_options = ["high", "medium", "low"]
            updated_urgency = st.selectbox(
                "Urgency",
                options=urgency_options,
                index=urgency_options.index(selected_urgency),
                format_func=lambda value: {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}[value],
                key=f"urgency_selected_{st.session_state.selected_ticket_id}",
            )
            if updated_urgency != selected_urgency:
                (selected_ticket.get("ticket") or {})["urgency"] = updated_urgency
                save_tickets(st.session_state.tickets)
                st.rerun()
        with ctrl_cols[1]:
            updated_status = st.selectbox(
                "Status",
                options=list(STATUS_STAGES),
                format_func=lambda s: STATUS_LABELS[s],
                index=STATUS_STAGES.index(selected_status),
                key=f"status_selected_{st.session_state.selected_ticket_id}",
            )
            if updated_status != selected_status:
                selected_ticket["status"] = updated_status
                save_tickets(st.session_state.tickets)
                st.rerun()

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
        st.info(f"Viewing saved ticket: {(selected.get('ticket') or {}).get('ticketId', 'Unknown')}")
        render_result(
            {
                "classification": selected.get("classification", "ticket"),
                "ticket": selected.get("ticket"),
                "resolution": selected.get("resolution", ""),
            },
            submitted_request=selected.get("message", ""),
        )
