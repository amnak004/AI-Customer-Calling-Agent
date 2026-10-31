

import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="AI Customer Calling Agent",
    description="QuickCart customer service assistant API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "faq_data.json"
)


def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


class ChatRequest(BaseModel):
    message: str


def detect_intent(message: str) -> str:
    text = message.lower().strip()

    # Human agent requests
    if any(term in text for term in [
        "human agent", "real person", "speak to someone",
        "talk to someone", "customer support", "representative"
    ]):
        return "human_agent"

    # Order status requests
    if any(term in text for term in [
        "order status", "track my order", "where is my order",
        "check my order", "order update", "shipment"
    ]):
        return "order_status"

    # Business hours requests
    if any(term in text for term in [
        "business hours", "opening hours", "open on sunday",
        "closed on sunday", "what time do you open",
        "when do you close", "working hours"
    ]):
        return "business_hours"

    # General questions
    if any(term in text for term in [
        "what is quickcart", "about quickcart"
    ]):
        return "general_faq"

    return "fallback"


def get_response(message: str):
    data = load_data()
    intent = detect_intent(message)
    text = message.lower()

    if intent == "order_status":
        match = re.search(r"\bQC\d{4}\b", message, re.IGNORECASE)

        if not match:
            return {
                "intent": intent,
                "response": "Please provide your order ID, such as QC1001."
            }

        order_id = match.group().upper()

        for order in data["sample_orders"]:
            if order["order_id"] == order_id:
                return {
                    "intent": intent,
                    "response": f"Your order {order_id} is {order['status']}.",
                    "order": order
                }

        return {
            "intent": intent,
            "response": "I could not find that order ID. Please check it and try again."
        }

    for faq in data["faqs"]:
        if faq["intent"] == intent:
            question_words = set(re.findall(r"\w+", text))
            faq_words = set(re.findall(r"\w+", faq["question"].lower()))

            if intent != "fallback" and question_words & faq_words:
                return {
                    "intent": intent,
                    "response": faq["answer"]
                }

    if intent == "human_agent":
        return {
            "intent": intent,
            "response": "I can register your request for assistance from a human agent. This demo does not connect to a live agent."
        }

    if intent == "business_hours":
        return {
            "intent": intent,
            "response": data["business"]["business_hours"]
        }

    if intent == "general_faq":
        return {
            "intent": intent,
            "response": "QuickCart is a sample online store used to demonstrate this customer-service assistant."
        }

    return {
        "intent": "fallback",
        "response": "Sorry, I do not have verified information for that question. You can request human assistance."
    }


@app.get("/")
def home():
    return {
        "message": "AI Customer Calling Agent backend is running!",
        "business": "QuickCart",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/business")
def get_business():
    return load_data()["business"]


@app.get("/faqs")
def get_faqs():
    return {"faqs": load_data()["faqs"]}


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    for order in load_data()["sample_orders"]:
        if order["order_id"].lower() == order_id.lower():
            return order

    raise HTTPException(status_code=404, detail="Order ID not found.")


@app.post("/chat")
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    return get_response(request.message)
