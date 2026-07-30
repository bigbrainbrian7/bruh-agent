import re
from bruhagent.models import Message

PHONE_NUMBER_REGEX = re.compile(r"^\+?[\d\s().-]{9,}$")

# TODO: explore more optimal conversions / prompt engineering for input into llm
# TODO: empty messages pop up frequently, for unknown reason. Results in empty input into llm
# diagnose pls
def messages_to_string(messages: list[Message]) -> str:
    speaker_labels = {}
    lines = []

    for message in messages:
        sender = message.sender
        if PHONE_NUMBER_REGEX.fullmatch(sender):
            sender = speaker_labels.setdefault(
                sender,
                f"SPEAKER_{len(speaker_labels) +1}"
            )
        text = message.text

        if text.strip():
            lines.append(f"[{sender}]: {text}")

    return "\n".join(lines)
