import json
from ollama import chat
from bruhagent.models import Message, Plan, PlanExtraction

from .conversation import messages_to_string

class PlanAnalyzer:

    @staticmethod
    def analyze_chat(
        messages: list[Message],
        model: str,
        previous_messages: list[Message] | None = None,
        previous_plan: Plan | None = None,
    ) -> PlanExtraction:
        previous_plan_text = "No previous plan state is saved for this chat."
        if previous_plan is not None:
            previous_plan_text = f"""
The following is the saved plan state from an earlier analysis. It may be stale;
the conversation messages are the source of truth when they conflict.

- Plan: {previous_plan.plan}
- Status: {previous_plan.status}
- Reason: {previous_plan.reason}
"""
        prompt = f"""
Analyze this imessage conversation and determine whether there is a plan, or if a plan might come together.

Do not take irrelevant information and rationalize it as a plan possibly coming together
However, the bar should be moderately low (eg. vague statements as "we should hangout")

Questions such as "When should we hangout" should also be considered as a possible start to a plan

Categorize it under statuses, and store it under the status field

- "none": the conversation has no notion of a plan or one coming together
- "active": A plan has been started, and participants are making progress
- "stuck": A plan exists, but progress has stalled because an important decision
  or piece of information is missing. 
- "completed": The plan has been finalized. Important logistics have been decided,
  such as time, location, and participants, or is already scheduled.

If a decision has not been agreed upon, or in other words only has one party making statements, do not consider that particular aspect as settled.

the plan field is the key information/main goal of a plan if it has been started. One sentence, brief

blocker is an unresolved open loop in the conversation: an unanswered proposal, conflicting plan details, or a stated issue with no resolution. Do not infer blockers from information that is simply absent.

Examples:
- "Let's go at 4?" -> "Confirm whether 4 pm works"
- "I can do 4." / "I can only do 5." -> "Choose a meeting time"
- "Let's go at 4." / "Agreed in person." ->[]

the reason field is why you have chosen the status and the representation of the plan the way you did. keep it concise, keep key information that lead to your decision

the confidence field is 0-100 of how confident you are of your selection and reasonings

Previous plan state:

{previous_plan_text}

Earlier messages for context:
{"There are no previous messages" if not previous_messages else messages_to_string(previous_messages)}

New messages since the last scan. If previous ongoing plan exists, use the new and earlier messages to update your understanding. Do not just treat them as two separate events:

{messages_to_string(messages)}
"""
# TODO: splice the messages to not reach token limit

        response = chat(
            model=model,
            messages=[
                {
                    "role":"user",
                    "content":prompt
                }
            ],
            format = PlanExtraction.model_json_schema(),
            think=False,
            keep_alive='1m'
        )

        # print("\nPERFORMANCE STATS")
        # for field in ["total_duration", "load_duration", "prompt_eval_duration", "eval_duration"]:
        #     print(f"{field}: {response[field]/1_000_000_000}")
        # print(f"Messages characters: {len(messages_to_string(messages))}\n")


        return PlanExtraction.model_validate_json(response.message.content)
