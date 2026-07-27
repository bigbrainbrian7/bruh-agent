import json
from datetime import datetime

from bruhagent.analysis import PlanAnalyzer
from bruhagent.database import ChatDBReader
from bruhagent.models import Message
from bruhagent.analysis import messages_to_string


def json_to_messages(json_messages: list[dict[str, str]], chat_id: str) -> list[Message]:
    """Convert an evaluation fixture's JSON messages into Message objects."""
    return [
        Message(
            id=index,
            chat_id=chat_id,
            sender=message["sender"],
            timestamp=datetime.now(),
            text=message["text"],
            is_from_me=False,
        )
        for index, message in enumerate(json_messages, start=1)
    ]

#TODO: add metric for semantic similarity between llm generated plan and reasoning and evaluation conversations
def evaluate_prediction(prediction, expected):
    return {
        "has_plan": (
            prediction.has_plan == expected.get("has_plan")
        ),
        "status": (
            prediction.status == expected.get("status")
        )
    }

def test_accuracy_from_json(json_file_path: str):

    with open(json_file_path) as f:
        dataset = json.load(f)

    totals = {
        "has_plan": 0,
        "status": 0
    }

    total_examples = len(dataset)

    for example in dataset:
        messages = json_to_messages(
            example["messages"],
            chat_id=f"fake-chat-{example['id']}",
        )
        prediction = PlanAnalyzer.analyze_chat(messages)
        expected = example["label"]

        results = evaluate_prediction(
            prediction,
            expected
        )

        for key, correct in results.items():
            if correct:
                totals[key] += 1

        print("=" * 50)
        print(f"Example {example['id']}")
        print(messages_to_string(messages))
        print("Prediction:", prediction)
        print("Expected:", expected)
        print("Correct:", results)

    print("\nEvaluation Results")
    print("=" * 50)

    for key, value in totals.items():
        print(
            f"{key}: {value}/{total_examples} "
            f"({value / total_examples:.2%})"
        )

    return totals

def test_accuracy_from_sqlite_db(json_file_path: str, db_file_path: str):
    """assumes db was made from json using create_test_db script"""

    with open(json_file_path) as f:
        dataset = json.load(f)

    reader = ChatDBReader(db_file_path)
    chat_ids = reader.get_chat_guids()

    totals = {
        "has_plan": 0,
        "status": 0
    }

    total_examples = len(dataset)

    for i, example in enumerate(dataset):
        messages = reader.get_messages(chat_ids[i])
        prediction = PlanAnalyzer.analyze_chat(messages)
        expected = example["label"]

        results = evaluate_prediction(
            prediction,
            expected
        )

        for key, correct in results.items():
            if correct:
                totals[key] += 1

        print("=" * 50)
        print(f"Example {example['id']}")
        print(messages_to_string(messages))
        print("Prediction:", prediction)
        print("Expected:", expected)
        print("Correct:", results)

    print("\nEvaluation Results")
    print("=" * 50)

    for key, value in totals.items():
        print(
            f"{key}: {value}/{total_examples} "
            f"({value / total_examples:.2%})"
        )

    return totals

def main():
    test_accuracy_from_sqlite_db("data/fake_conversations.json", "data/fake_chat.db")
    test_accuracy_from_json("data/fake_conversations.json")


if __name__ == "__main__":
    main()
