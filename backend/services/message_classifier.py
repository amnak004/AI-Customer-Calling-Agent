
from transformers import pipeline

MODEL_NAME = "Horizon-Labs/multilingual-toxicity-small"

print("Loading QuickCart message classifier...")

toxicity_classifier = pipeline(
    "text-classification",
    model=MODEL_NAME,
    top_k=None,
    device=-1
)

print("QuickCart message classifier ready.")


def classify_message(message: str) -> str:
    results = toxicity_classifier(
        message,
        truncation=True,
        max_length=256
    )[0]

    scores = {
        item["label"].lower(): float(item["score"])
        for item in results
    }

    insult_score = scores.get("insult", 0.0)
    toxicity_score = scores.get("toxicity", 0.0)

    # Debug scores
    print(
        f"Message: {message} | "
        f"Insult: {insult_score:.3f} | "
        f"Toxicity: {toxicity_score:.3f}"
    )

    # Initial thresholds
    if insult_score >= 0.65 or toxicity_score >= 0.75:
        return "abuse"

    return "normal"
