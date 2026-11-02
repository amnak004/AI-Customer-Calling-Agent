
import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from backend.services.database import save_conversation
except ModuleNotFoundError:
    from services.database import save_conversation

# Support both: uvicorn backend.main:app and running from backend folder
try:
    from backend.services.rag_service import retrieve_faq
except ModuleNotFoundError:
    from services.rag_service import retrieve_faq


BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "backend" / "config" / "company.json"
LEGACY_DATA_FILE = BASE_DIR / "data" / "faq_data.json"

with CONFIG_FILE.open("r", encoding="utf-8-sig") as file:
    CONFIG = json.load(file)

KNOWLEDGE_BASE = BASE_DIR / CONFIG["knowledge_base"]
FAQ_FILE = KNOWLEDGE_BASE / "faqs.json"
BUSINESS_FILE = KNOWLEDGE_BASE / "business.json"


app = FastAPI(
    title="AI Customer Calling Agent",
    description="Configurable AI customer service assistant",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


def load_json(file_path):
    with file_path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_faqs():
    return load_json(FAQ_FILE)


def load_business():
    return load_json(BUSINESS_FILE)


def load_orders():
    # Order records remain separate from the RAG knowledge base
    data = load_json(LEGACY_DATA_FILE)
    return data.get("sample_orders", [])


def detect_intent(message: str) -> str:
    text = message.lower().strip()

    if any(term in text for term in [
        "human agent", "real person", "speak to someone",
        "talk to someone", "customer support",
        "representative", "speak to a human"
    ]):
        return "human_agent"

    if any(term in text for term in [
        "order", "shipment", "tracking",
        "track my parcel", "where is my parcel"
    ]):
        return "order_status"

    if any(term in text for term in [
        "business hours", "opening hours",
        "open on sunday", "closed on sunday",
        "what time do you open", "when do you open",
        "when does your store open", "when do you close",
        "working hours", "what time are you open"
    ]):
        return "business_hours"

    return "general_faq"


def get_response(message: str):
    text = message.lower().strip()
    intent = detect_intent(message)

    # 1. Order tracking: traditional lookup
    if intent == "order_status":
        match = re.search(r"\bQC\d{4}\b", message, re.IGNORECASE)

        if not match:
            return {
                "intent": intent,
                "response": "Please provide your order ID, such as QC1001.",
                "source": "rule_based"
            }

        order_id = match.group().upper()

        for order in load_orders():
            if order["order_id"] == order_id:
                return {
                    "intent": intent,
                    "response": f"Your order {order_id} is {order['status']}.",
                    "order": order,
                    "source": "order_database"
                }

        return {
            "intent": intent,
            "response": "I could not find that order ID. Please check it and try again.",
            "source": "order_database"
        }

    # 2. Human escalation: traditional logic
    if intent == "human_agent":
        return {
            "intent": intent,
            "response": (
                "I can register your request for assistance from a human agent. "
                "This demo does not connect to a live agent."
            ),
            "source": "rule_based"
        }

    # 3. Business hours: verified company configuration
    if intent == "business_hours":
        business = load_business()

        if "sunday" in text:
            response = (
                "We are closed on Sundays."
                if "Sunday" not in business["working_days"]
                else business["business_hours"]
            )
        else:
            response = business["business_hours"]

        return {
            "intent": intent,
            "response": response,
            "source": "business_configuration"
        }

    # 4. General questions: semantic RAG retrieval
    results = retrieve_faq(message, top_k=3, threshold=0.35)

    if results:
        best_match = results[0]

        return {
            "intent": best_match["intent"],
            "response": best_match["answer"],
            "source": "rag",
            "matched_question": best_match["question"],
            "similarity": round(best_match["similarity"], 3)
        }

    # 5. No verified information found
    return {
        "intent": "fallback",
        "response": (
            "Sorry, I do not have verified information for that question. "
            "You can request human assistance."
        ),
        "source": "fallback"
    }


@app.get("/")
def home():
    return {
        "message": "AI Customer Calling Agent backend is running!",
        "business": CONFIG["company_name"],
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/business")
def get_business():
    return load_business()


@app.get("/faqs")
def get_faqs():
    return {"faqs": load_faqs()}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    for order in load_orders():
        if order["order_id"].lower() == order_id.lower():
            return order

    raise HTTPException(status_code=404, detail="Order ID not found.")


@app.post("/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    result = get_response(request.message)

    # Automatically save every conversation
    try:
        save_conversation(
            customer_message=request.message,
            bot_response=result["response"],
            intent=result.get("intent"),
            source=result.get("source"),
            provider=result.get("provider"),
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0)
        )
    except Exception as error:
        print(f"Database logging error: {error}")

    return result