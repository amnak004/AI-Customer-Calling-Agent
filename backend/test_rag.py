
from services.rag_service import retrieve_faq

questions = [
    "When does your store open?",
    "Can I get help from a real person?",
    "What is this online store?"
]

for question in questions:
    print("\nQuestion:", question)

    results = retrieve_faq(question)

    for result in results:
        print("Matched:", result["question"])
        print("Answer:", result["answer"])
        print("Similarity:", round(result["similarity"], 3))
