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
        .main {
            background-color: #f6f8fb;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        .app-title {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
            color: #1f2a44;
        }
        .app-subtitle {
            color: #5b6475;
            margin-bottom: 1.5rem;
        }
        .card {
            background: white;
            border: 1px solid #e6eaf2;
            border-radius: 18px;
            padding: 1.25rem 1.25rem 1rem 1.25rem;
            box-shadow: 0 4px 18px rgba(17, 24, 39, 0.05);
            margin-bottom: 1rem;
        }
        .card h3 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: #1f2a44;
        }
        .metric-label {
            font-size: 0.82rem;
            color: #6b7280;
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 1.05rem;
            font-weight: 700;
            color: #111827;
        }
        .badge {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
        }
        .badge-low {
            background: #dcfce7;
            color: #166534;
        }
        .badge-medium {
            background: #fef3c7;
            color: #92400e;
        }
        .badge-high {
            background: #fee2e2;
            color: #991b1b;
        }
        .ticket-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #111827;
            margin-top: 0.35rem;
            margin-bottom: 0.5rem;
        }
        .section-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 1rem;
            margin-bottom: 0.35rem;
        }
        .response-box {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1rem;
            white-space: pre-wrap;
            line-height: 1.55;
            color: #111827;
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 14px;
        }
        div[data-testid="stButton"] > button {
            border-radius: 12px;
            font-weight: 700;
            height: 3rem;
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


def get_open_tickets(tickets: list[dict]) -> list[dict]:
    return [ticket for ticket in tickets if ticket.get("status", "open") == "open"]


def get_completed_tickets(tickets: list[dict]) -> list[dict]:
    return [ticket for ticket in tickets if ticket.get("status") == "completed"]


URGENCY_SCORES = {
    "high": 100,
    "medium": 60,
    "low": 30,
}


def normalize_urgency(urgency: str | None) -> str:
    normalized = (urgency or "").strip().lower()
    return normalized if normalized in {"low", "medium", "high"} else "medium"


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
    css_class = {
        "low": "badge-low",
        "medium": "badge-medium",
        "high": "badge-high",
    }.get(urgency, "badge-medium")
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
            st.markdown(
                '<div class="section-label">Likely Root Cause</div>', unsafe_allow_html=True
            )
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

    with st.expander("Raw JSON output"):
        st.json(result)


if "tickets" not in st.session_state:
    st.session_state.tickets = load_tickets()
if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None
if "message_input" not in st.session_state:
    st.session_state.message_input = ""

st.markdown('<div class="app-title">🩺 Healthcare Support Triage</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">AI-powered triage for support messages, ticket creation, and suggested customer responses.</div>',
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

    queue_tickets = rank_tickets(get_open_tickets(st.session_state.tickets))
    if queue_tickets:
        labels = [
            f"{idx + 1}. [{(entry.get('ticket') or {}).get('urgency', 'medium').upper()}] "
            f"{(entry.get('ticket') or {}).get('title', 'No title')}"
            for idx, entry in enumerate(queue_tickets)
        ]
        selected_label = st.radio("Open saved ticket", labels, key="selected_ticket_label")
        selected_index = labels.index(selected_label)
        st.session_state.selected_ticket_id = queue_tickets[selected_index].get("saved_id")
    else:
        st.caption("No tickets in the queue.")

    completed_tickets = rank_tickets(get_completed_tickets(st.session_state.tickets))
    st.divider()
    st.subheader("Completed Tasks")
    if completed_tickets:
        completed_labels = [
            f"{idx + 1}. [{(entry.get('ticket') or {}).get('urgency', 'medium').upper()}] "
            f"{(entry.get('ticket') or {}).get('title', 'No title')}"
            for idx, entry in enumerate(completed_tickets)
        ]
        completed_selected_label = st.radio(
            "Open completed ticket", completed_labels, key="selected_completed_ticket_label"
        )
        completed_selected_index = completed_labels.index(completed_selected_label)
        st.session_state.selected_ticket_id = completed_tickets[completed_selected_index].get(
            "saved_id"
        )
    else:
        st.caption("No completed tasks yet.")

with st.form("triage_form", clear_on_submit=True):
    message = st.text_area(
        "Incoming support message",
        key="message_input",
        height=220,
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
                    "status": "open",
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
elif st.session_state.selected_ticket_id:
    selected = next(
        (
            entry
            for entry in st.session_state.tickets
            if entry.get("saved_id") == st.session_state.selected_ticket_id
        ),
        None,
    )
    if selected:
        st.info(
            f"Viewing saved ticket: {(selected.get('ticket') or {}).get('ticketId', 'Unknown')}"
        )
        selected_status = selected.get("status", "open")
        if selected_status == "open":
            if st.button("Resolve ticket", type="primary"):
                selected["status"] = "completed"
                save_tickets(st.session_state.tickets)
                st.success("Ticket resolved and moved to Completed Tasks.")
                st.rerun()
        else:
            st.caption("This ticket is completed.")
        render_result(
            {
                "classification": selected.get("classification", "ticket"),
                "ticket": selected.get("ticket"),
                "resolution": selected.get("resolution", ""),
            },
            submitted_request=selected.get("message", ""),
        )
