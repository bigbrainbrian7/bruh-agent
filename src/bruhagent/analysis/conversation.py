from bruhagent.models import Message

# TODO: explore more optimal conversions / prompt engineering for input into llm
def messages_to_string(messages: list[Message]) -> str:
    lines = []

    for message in messages:
        sender = message.sender
        text = message.text

        if text.strip():
            lines.append(f"{sender}: {text}")

    return "\n".join(lines)
