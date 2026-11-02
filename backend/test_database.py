
from services.database import (
    save_conversation,
    get_conversations,
    save_api_usage,
    get_api_usage
)

save_conversation(
    customer_message="What is QuickCart?",
    bot_response="QuickCart is a sample online store.",
    intent="general_faq",
    source="rag"
)

save_api_usage(
    provider="Gemini",
    input_tokens=100,
    output_tokens=50
)

print("Conversation records:")
print(get_conversations())

print("\nAPI usage records:")
print(get_api_usage())

print("\nDatabase test completed!")
