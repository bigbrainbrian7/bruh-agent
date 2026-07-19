import json

from openai import OpenAI

client = OpenAI(
    #default address for ollama server
    base_url="http://localhost:11434/v1",
    api_key="bruh"
)


def analyze_chat(messages):

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

Conversation:

{messages}
"""

    response = client.chat.completions.create(
        model="qwen3:8b",
        
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


    return json.loads(
        response.choices[0].message.content
    )