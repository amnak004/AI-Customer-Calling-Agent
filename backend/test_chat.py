
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

test_cases = [
    {
        "name": "Business hours",
        "message": "What are your business hours?",
        "expected_intent": "business_hours"
    },
    {
        "name": "Sunday availability",
        "message": "Are you open on Sunday?",
        "expected_intent": "business_hours"
    },
    {
        "name": "Order status with valid ID",
        "message": "What is my order status for QC1001?",
        "expected_intent": "order_status"
    },
    {
        "name": "Order status without ID",
        "message": "Check my order status",
        "expected_intent": "order_status"
    },
    {
        "name": "Human agent",
        "message": "Can I speak to a human agent?",
        "expected_intent": "human_agent"
    },
    {
        "name": "General FAQ",
        "message": "What is QuickCart?",
        "expected_intent": "general_faq"
    },
    {
        "name": "Unknown question",
        "message": "Do you sell laptops?",
        "expected_intent": "fallback"
    }
]

passed = 0

print("\nAI CUSTOMER CALLING AGENT - TEST RESULTS")
print("=" * 55)

for test in test_cases:
    payload = json.dumps({
        "message": test["message"]
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))

        actual_intent = result.get("intent")
        success = actual_intent == test["expected_intent"]

        if success:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"\n[{status}] {test['name']}")
        print(f"Message: {test['message']}")
        print(f"Expected intent: {test['expected_intent']}")
        print(f"Actual intent:   {actual_intent}")
        print(f"Response: {result.get('response')}")

    except urllib.error.URLError as error:
        print(f"\n[ERROR] {test['name']}: {error}")

print("\n" + "=" * 55)
print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
