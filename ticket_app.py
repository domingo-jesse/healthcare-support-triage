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
)

st.markdown(
    """
    <style>
        :root {
            --bg-primary: #f3f6fc;
            --bg-secondary: #ffffff;
            --bg-tertiary: #eef2ff;
            --text-primary: #111827;
            --text-muted: #64748b;
            --border: #dbe4f2;
            --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
            --accent: #4f46e5;
            --accent-soft: rgba(79, 70, 229, 0.12);
            --card-gradient: linear-gradient(145deg, #ffffff 0%, #f8fbff 100%);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #060b18;
                --bg-secondary: #0f172a;
                --bg-tertiary: #101d3a;
                --text-primary: #e2e8f0;
                --text-muted: #94a3b8;
                --border: #22314d;
                --shadow: 0 14px 30px rgba(0, 0, 0, 0.45);
                --accent: #818cf8;
                --accent-soft: rgba(129, 140, 248, 0.18);
                --card-gradient: linear-gradient(145deg, #0f172a 0%, #14233f 100%);
            }
        }
        .main, .stApp {
            background: radial-gradient(circle at top right, #172554 0%, transparent 30%), var(--bg-primary);
            color: var(--text-primary);
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        .app-title {
            font-size: 2.1rem;
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
            border-radius: 18px;
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
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
        }
        .badge-low { background: #dcfce7; color: #166534; }
        .badge-medium { background: #fef3c7; color: #92400e; }
        .badge-high { background: #fee2e2; color: #991b1b; }
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
            border-radius: 14px;
            border: 1px solid var(--border);
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        div[data-testid="stButton"] > button {
            border-radius: 10px;
            font-weight: 700;
            height: 2.5rem;
        }
        .toolbar-card {
            border: 1px solid var(--border);
            border-radius: 16px;
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
            border-radius: 14px;
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
if "selected_ticket_label" not in st.session_state:
    st.session_state.selected_ticket_label = "None"

st.markdown('<div class="app-title">🩺 Healthcare Support Triage</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Dark-mode optimized triage board with sortable tickets and stage movement controls.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Examples")
    example_choice = st.selectbox("Load a sample", ["Custom"] + list(EXAMPLES.keys()))
    st.markdown("Use one of these sample issues or paste your own message.")

    if example_choice != "Custom":
        st.session_state.message_input = EXAMPLES[example_choice]

    st.divider()
    st.subheader("Queue")

    queue_tickets = rank_tickets(
        [t for t in st.session_state.tickets if normalize_status(t.get("status")) != "completed"]
    )
    completed_tickets = rank_tickets(get_completed_tickets(st.session_state.tickets))

    st.caption(f"Open: {len(queue_tickets)}  •  Completed: {len(completed_tickets)}")

    ticket_lookup: dict[str, str] = {}
    ticket_options = ["None"]

    if queue_tickets:
        ticket_options.append("— Open tickets —")
        for idx, entry in enumerate(queue_tickets):
            label = (
                f"{idx + 1}. [{(entry.get('ticket') or {}).get('urgency', 'medium').upper()}] "
                f"{(entry.get('ticket') or {}).get('title', 'No title')}"
            )
            ticket_options.append(label)
            ticket_lookup[label] = entry.get("saved_id", "")

    if completed_tickets:
        ticket_options.append("— Completed tickets —")
        for idx, entry in enumerate(completed_tickets):
            label = (
                f"{idx + 1}. [{(entry.get('ticket') or {}).get('urgency', 'medium').upper()}] "
                f"{(entry.get('ticket') or {}).get('title', 'No title')}"
            )
            ticket_options.append(label)
            ticket_lookup[label] = entry.get("saved_id", "")

    selected_label = st.selectbox("Open saved ticket", ticket_options, key="selected_ticket_label")
    st.session_state.selected_ticket_id = ticket_lookup.get(selected_label)

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
        ["Manual order", "Urgency (high to low)", "Newest first", "Oldest first"],
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
    '<div class="mini-note">Features added: dark-mode visual refresh, kanban ticket stages, search/filter/sort toolbar, and manual up/down ordering controls.</div>',
    unsafe_allow_html=True,
)

board_cols = st.columns(4, gap="small")
for idx, status in enumerate(STATUS_STAGES):
    with board_cols[idx]:
        tickets_for_status = [
            t for t in filtered_tickets if normalize_status(t.get("status")) == status
        ]
        st.markdown(
            f'<div class="board-column"><div class="board-title">{STATUS_LABELS[status]} <span class="column-chip">{len(tickets_for_status)}</span></div>',
            unsafe_allow_html=True,
        )

        if not tickets_for_status:
            st.caption("No tickets here.")

        for ticket in tickets_for_status:
            ticket_id = ticket.get("saved_id", "")
            urgency = normalize_urgency((ticket.get("ticket") or {}).get("urgency"))
            title = (ticket.get("ticket") or {}).get("title", "Untitled ticket")

            st.markdown(
                f"""
                <div class="ticket-card">
                    <strong>{html.escape(title)}</strong><br/>
                    {urgency_badge_html(urgency)}
                    <div class="ticket-meta">{ticket_id}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_cols = st.columns([1, 1, 1])
            with action_cols[0]:
                if st.button("Open", key=f"open_{ticket_id}", use_container_width=True):
                    st.session_state.selected_ticket_id = ticket_id
                    st.rerun()
            with action_cols[1]:
                move_label = "↺ Reopen" if status == "completed" else "Next ▶"
                if st.button(move_label, key=f"next_{ticket_id}", use_container_width=True):
                    stage_idx = STATUS_STAGES.index(status)
                    ticket["status"] = (
                        STATUS_STAGES[0]
                        if status == "completed"
                        else STATUS_STAGES[min(stage_idx + 1, len(STATUS_STAGES) - 1)]
                    )
                    save_tickets(st.session_state.tickets)
                    st.rerun()
            with action_cols[2]:
                if st.button("◀ Prev", key=f"prev_{ticket_id}", use_container_width=True):
                    stage_idx = STATUS_STAGES.index(status)
                    ticket["status"] = STATUS_STAGES[max(stage_idx - 1, 0)]
                    save_tickets(st.session_state.tickets)
                    st.rerun()

            order_cols = st.columns([1, 1])
            with order_cols[0]:
                if st.button("↑", key=f"up_{ticket_id}", use_container_width=True):
                    current_index = st.session_state.tickets.index(ticket)
                    if current_index > 0:
                        st.session_state.tickets[current_index - 1], st.session_state.tickets[current_index] = (
                            st.session_state.tickets[current_index],
                            st.session_state.tickets[current_index - 1],
                        )
                        save_tickets(st.session_state.tickets)
                        st.rerun()
            with order_cols[1]:
                if st.button("↓", key=f"down_{ticket_id}", use_container_width=True):
                    current_index = st.session_state.tickets.index(ticket)
                    if current_index < len(st.session_state.tickets) - 1:
                        st.session_state.tickets[current_index + 1], st.session_state.tickets[current_index] = (
                            st.session_state.tickets[current_index],
                            st.session_state.tickets[current_index + 1],
                        )
                        save_tickets(st.session_state.tickets)
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

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
