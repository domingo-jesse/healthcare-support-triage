from pydantic import BaseModel
from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace


class ClassifierSchema(BaseModel):
    classification: str


class TicketAgentSchema(BaseModel):
    ticketId: str
    title: str
    urgency: str


classifier = Agent(
    name="Classifier",
    instructions=(
        'You are a classifier. '
        'Classify the user message as either: '
        '"ticket" if it is a real support issue '
        '(bugs, errors, system not working, blocking work) '
        'or "spam" if it is irrelevant, promotional, or not a real issue. '
        'Respond ONLY with valid JSON in this format: '
        '{"classification": "ticket"} or {"classification": "spam"}.'
    ),
    model="gpt-4.1",
    output_type=ClassifierSchema,
    model_settings=ModelSettings(
        temperature=1,
        top_p=1,
        max_tokens=2048,
        store=True,
    ),
)

ticket_agent = Agent(
    name="Ticket agent",
    instructions="""
You are a ticket severity agent.

Review the issue and return:
- ticketId
- title
- urgency

Rules:
- low: login issue, password reset, enhancement request
- medium: partial feature failure, UI bug, not fully blocking
- high: system fully down, users blocked, widespread outage, all caps urgency

Keep the title short and realistic.
Return valid JSON only.
""",
    model="gpt-4.1",
    output_type=TicketAgentSchema,
    model_settings=ModelSettings(
        temperature=1,
        top_p=1,
        max_tokens=2048,
        store=True,
    ),
)

spam_agent = Agent(
    name="Spam Agent",
    instructions=(
        "If the message is spam, explain briefly why it is spam and why it should not be treated as a ticket."
    ),
    model="gpt-4.1",
    model_settings=ModelSettings(
        temperature=1,
        top_p=1,
        max_tokens=2048,
        store=True,
    ),
)

resolution_agent = Agent(
    name="Resolution Agent",
    instructions="""
You are a healthcare technical support resolution agent.

Your job is to analyze the issue and provide:
1. A clear root cause if possible
2. Recommended next steps for the support team
3. A suggested response that can be sent to the customer

Keep it concise and practical.
""",
    model="gpt-4.1",
    model_settings=ModelSettings(
        temperature=1,
        top_p=1,
        max_tokens=2048,
        store=True,
    ),
)


class WorkflowInput(BaseModel):
    input_as_text: str


async def run_workflow(workflow_input: WorkflowInput):
    with trace("New agent"):
        workflow = workflow_input.model_dump()

        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": workflow["input_as_text"],
                    }
                ],
            }
        ]

        classifier_result_temp = await Runner.run(
            classifier,
            input=[*conversation_history],
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "agent-builder",
                    "workflow_id": "wf_69ca443212748190a88bbb4492f3a1c70743dc1c484b9af8",
                }
            ),
        )

        conversation_history.extend(
            [item.to_input_item() for item in classifier_result_temp.new_items]
        )

        classifier_result = {
            "output_text": classifier_result_temp.final_output.json(),
            "output_parsed": classifier_result_temp.final_output.model_dump(),
        }

        if classifier_result["output_parsed"]["classification"] == "ticket":
            ticket_agent_result_temp = await Runner.run(
                ticket_agent,
                input=[*conversation_history],
                run_config=RunConfig(
                    trace_metadata={
                        "__trace_source__": "agent-builder",
                        "workflow_id": "wf_69ca443212748190a88bbb4492f3a1c70743dc1c484b9af8",
                    }
                ),
            )

            conversation_history.extend(
                [item.to_input_item() for item in ticket_agent_result_temp.new_items]
            )

            ticket_agent_result = {
                "output_text": ticket_agent_result_temp.final_output.json(),
                "output_parsed": ticket_agent_result_temp.final_output.model_dump(),
            }

            resolution_agent_result_temp = await Runner.run(
                resolution_agent,
                input=[*conversation_history],
                run_config=RunConfig(
                    trace_metadata={
                        "__trace_source__": "agent-builder",
                        "workflow_id": "wf_69ca443212748190a88bbb4492f3a1c70743dc1c484b9af8",
                    }
                ),
            )

            conversation_history.extend(
                [item.to_input_item() for item in resolution_agent_result_temp.new_items]
            )

            resolution_agent_result = {
                "output_text": resolution_agent_result_temp.final_output_as(str)
            }

            return {
                "classification": classifier_result["output_parsed"]["classification"],
                "ticket": ticket_agent_result["output_parsed"],
                "resolution": resolution_agent_result["output_text"],
            }

        spam_agent_result_temp = await Runner.run(
            spam_agent,
            input=[*conversation_history],
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "agent-builder",
                    "workflow_id": "wf_69ca443212748190a88bbb4492f3a1c70743dc1c484b9af8",
                }
            ),
        )

        conversation_history.extend(
            [item.to_input_item() for item in spam_agent_result_temp.new_items]
        )

        spam_agent_result = {
            "output_text": spam_agent_result_temp.final_output_as(str)
        }

        return {
            "classification": classifier_result["output_parsed"]["classification"],
            "ticket": None,
            "resolution": spam_agent_result["output_text"],
        }
