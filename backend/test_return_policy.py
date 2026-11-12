import pytest

from backend import main


@pytest.mark.parametrize(
    "question",
    [
        "What is your return policy?",
        "Can I return my order?",
        "How many days do I have to return a product?",
        "When will I receive my refund?",
    ],
)
def test_return_policy_questions_return_verified_policy(
    question,
    monkeypatch
):
    monkeypatch.setattr(main, "classify_message", lambda message: "normal")

    def fail_ai(*args, **kwargs):
        raise RuntimeError("AI providers are unavailable.")

    monkeypatch.setattr(main, "generate_response", fail_ai)

    response = main.get_response(question)

    expected_answer = (
        "Customers can return products within 7 days of delivery. "
        "To request a return, contact QuickCart support and provide your "
        "order ID. After the return is approved, refunds are processed "
        "within 5 business days."
    )
    assert response["intent"] == "general_faq"
    assert response["source"] == "rag_fallback"
    assert response["response"] == expected_answer
