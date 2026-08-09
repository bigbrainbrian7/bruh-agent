from datetime import datetime

from bruhagent.models import Message, Plan, PlanExtraction
from bruhagent.llm import LLMProvider

from .conversation import messages_to_string

class PlanAnalyzer:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def analyze_chat(
        self,
        messages: list[Message],
        previous_messages: list[Message] | None = None,
        previous_plan: Plan | None = None,
    ) -> PlanExtraction:
        # TODO: splice the messages to not reach token limit

        prompt = self._build_prompt(messages, previous_messages=previous_messages, previous_plan=previous_plan)

        return self.provider.analyze_plan(prompt)


    def _build_prompt(self, messages: list[Message], previous_messages: list[Message] | None = None, previous_plan: Plan | None = None) -> str:
        local_time = datetime.now().astimezone().isoformat()
        previous_plan_text = "No previous plan state is saved for this chat."
        if previous_plan is not None:
            previous_plan_text = f"""
The following is the saved plan state from an earlier analysis. It may be stale;
the conversation messages are the source of truth when they conflict.

- Plan: {previous_plan.plan}
- Status: {previous_plan.status}
- Reason: {previous_plan.reason}
"""
        return f"""
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

Messages are informal and may be fragmented. A plan is often spread across several
short messages, with unrelated jokes or side topics between the proposal and its
reply. Track open conversational threads across the whole exchange rather than
requiring adjacent messages or a formal recap of the plan. A short affirmative
reply, a time, a place, or another logistical detail can answer an earlier proposal
when it is a plausible continuation of that thread, even if it appears later.

Do not require every participant, purpose, and detail to be explicitly restated
before recognizing a plan. A concrete shared activity plus implicit or explicit
engagement is enough for an active plan. Use "none" only when there is no plausible
shared activity being coordinated anywhere in the conversation. Do not join messages
into a plan when their meaning clearly belongs to different conversational threads.

the plan field is the key information/main goal of a plan if it has been started. One sentence, brief

blocker is an unresolved open loop in the conversation: an unanswered proposal, conflicting plan details, or a stated issue with no resolution. Do not infer blockers from information that is simply absent.

Examples:
- "Let's go at 4?" -> "Confirm whether 4 pm works"
- "I can do 4." / "I can only do 5." -> "Choose a meeting time"
- "Let's go at 4." / "Agreed in person." ->[]

the reason field is why you have chosen the status and the representation of the plan the way you did. keep it concise, keep key information that lead to your decision

the confidence field is 0-100 of how confident you are of your selection and reasonings

tool_calls are optional native actions the app may offer to the user. 

Only propose create_calendar_event when the conversation clearly agrees on a social event with a specific date and time. 
Use an exact ISO-8601 start_time and end_time with the
timezone. 
Never guess a date, time, duration, title, or location, but still make an event if at least the time is known, indicating one identifier in the title (fall back to the chat name if none).
Use "calendar-event" as the tool call id.
The current local time is {local_time}.

Previous plan state:

{previous_plan_text}

Earlier messages for context:
{"There are no previous messages" if not previous_messages else messages_to_string(previous_messages)}

New messages since the last scan. If previous ongoing plan exists, use the new and earlier messages to update your understanding. Do not just treat them as two separate events:

{messages_to_string(messages)}
"""
