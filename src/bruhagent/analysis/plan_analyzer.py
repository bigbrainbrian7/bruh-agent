import json
from bruhagent.llm import client
from bruhagent.models import Message, Plan

from .conversation import messages_to_string

class PlanAnalyzer:

    @staticmethod
    def analyze_chat(
        messages: list[Message],
        previous_messages: list[Message] | None = None,
        previous_plan: Plan | None = None,
        model="qwen3:8b",
    ) -> Plan:
        previous_plan_text = "No previous plan state is saved for this chat."
        if previous_plan is not None:
            previous_plan_text = f"""
The following is the saved plan state from an earlier analysis. It may be stale;
the conversation messages are the source of truth when they conflict.

- Has plan: {previous_plan.has_plan}
- Plan: {previous_plan.plan}
- Status: {previous_plan.status}
- Reason: {previous_plan.reason}
"""
        prompt = f"""
You analyze group conversations.

Determine whether there is a plan and what state the plan is in.

Definitions of statuses:

- "none": There is no actual plan. The conversation only contains vague ideas,
  suggestions, wishes, or hypothetical discussions (e.g. "we should hang out sometime").

- "active": A plan exists and participants are actively making progress.
  The group is still discussing details and the conversation is moving forward.
  Use this when unresolved details are being actively worked on.

- "stuck": A plan exists, but progress has stalled because an important decision
  or piece of information is missing. Use this when the group cannot move forward
  without resolving something (for example: no location, no date, no participants,
  no agreement on key details).

- "completed": The plan has been finalized. Important logistics have been decided,
  such as time, location, and participants, or the event is already scheduled.

Examples:

Active:
"Movie night Friday?"
"I'm free"
"Cool, I'll pick a movie later"
→ The plan is progressing.

Stuck:
"We should hike this weekend"
"I'm down"
"Saturday works"
"Where should we go?"
→ The plan exists but cannot proceed until a location is chosen.

Completed:
"Dinner Friday at Luigi's at 7?"
"Sounds good"
→ The plan is finalized.

Return JSON only:

{{
"has_plan": bool,
"plan": string|null,
"status": "active" | "stuck" | "completed" | "none",
"reason": string|null
}}

Previous plan state:

{previous_plan_text}

Earlier messages for context:
{"There are no previous messages" if not previous_messages else messages_to_string(previous_messages)}

New messages since the last scan, to update or create the plan state:

{messages_to_string(messages)}
"""

        response = client.chat.completions.create(
            model=model,
            
            #TODO: move to structured outputs: 
            #https://developers.openai.com/api/docs/guides/structured-outputs
            #https://ollama.com/blog/structured-outputs
            response_format={
                "type":"json_object"
            },
            messages=[
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )


        analysis = json.loads(response.choices[0].message.content)
        return Plan(
            has_plan=analysis["has_plan"],
            plan=analysis["plan"],
            status=analysis["status"],
            reason=analysis.get("reason"),
        )
