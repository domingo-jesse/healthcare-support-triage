import asyncio
import streamlit as st
from workflow_backend import run_workflow, WorkflowInput

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


def urgency_badge_html(urgency: str) -> str:
    urgency = (urgency or "").lower()
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

    root_cause = root_cause.replace("for Support Team:", "").replace("to Customer:", "").strip(" :\n")
    next_steps = next_steps.replace("for Support Team:", "").replace("to Customer:", "").strip(" :\n")
    suggested_response = suggested_response.replace("to Customer:", "").strip(" :\n")

    if not root_cause and not next_steps and not suggested_response:
        return "", resolution.strip(), ""

    return root_cause.strip(), next_steps.strip(), suggested_response.strip()


st.markdown('<div class="app-title">🩺 Healthcare Support Triage</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">AI-powered triage for support messages, ticket creation, and suggested customer responses.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Examples")
    example_choice = st.selectbox("Load a sample", ["Custom"] + list(EXAMPLES.keys()))
    st.markdown("Use one of these sample issues or paste your own message.")

default_message = EXAMPLES.get(example_choice, "") if example_choice != "Custom" else ""

message = st.text_area(
    "Incoming support message",
    value=default_message,
    height=220,
    placeholder="Paste a support ticket here...",
)

if st.button("Run triage", type="primary", use_container_width=True):
    if not message.strip():
        st.warning("Please enter a message.")
    else:
        try:
            with st.spinner("Analyzing issue..."):
                result = asyncio.run(
                    run_workflow(WorkflowInput(input_as_text=message.strip()))
                )

            st.success("Analysis complete")

            left, right = st.columns([1, 1.2], gap="large")

            with left:
                st.markdown('<div class="card"><h3>📌 Overview</h3>', unsafe_allow_html=True)
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
                    st.markdown('<div class="section-label">Recommended Next Steps</div>', unsafe_allow_html=True)
                    st.write(next_steps)
                else:
                    st.markdown('<div class="section-label">Resolution Notes</div>', unsafe_allow_html=True)
                    st.write(result["resolution"])

                if suggested_response:
                    st.markdown('<div class="section-label">Suggested Customer Response</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="response-box">{suggested_response}</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("Raw JSON output"):
                st.json(result)

        except Exception as e:
            st.error(f"Error: {e}")