import json

from bruhagent.analysis import PlanAnalyzer

#TODO: add metric for semantic similarity between llm generated plan and reasoning and evaluation conversations
def evaluate_prediction(prediction, expected):
    return {
        "has_plan": (
            prediction.get("has_plan") == expected.get("has_plan")
        ),
        "status": (
            prediction.get("status") == expected.get("status")
        )
    }

def main():
    with open("data/fake_conversations.json") as f:
        dataset = json.load(f)

    totals = {
        "has_plan": 0,
        "status": 0
    }

    total_examples = len(dataset)

    for example in dataset:
        prediction = PlanAnalyzer.analyze_chat(example["messages"])
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


if __name__ == "__main__":
    main()