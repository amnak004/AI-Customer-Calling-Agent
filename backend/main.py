import os
import io
import os
import zipfile
import os
import json
import os
import re
from pathlib import Path

from backend.services.message_classifier import classify_message
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from backend.services.database import save_conversation, save_api_usage
    from backend.services.rag_service import retrieve_faq, rebuild_index
    from backend.services.ai_provider import generate_response
except ModuleNotFoundError:
    from services.database import save_conversation, save_api_usage
    from services.rag_service import retrieve_faq, rebuild_index
    from services.ai_provider import generate_response



BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "backend" / "config" / "company.json"


with CONFIG_FILE.open("r", encoding="utf-8-sig") as file:
    CONFIG = json.load(file)

KNOWLEDGE_BASE = BASE_DIR / CONFIG["knowledge_base"]
FAQ_FILE = KNOWLEDGE_BASE / "faqs.json"
BUSINESS_FILE = KNOWLEDGE_BASE / "business.json"

AI_SETTINGS = CONFIG.get("ai_settings", {})


app = FastAPI(
    title="AI Customer Calling Agent",
    description="Configurable AI customer service assistant",
    version="2.1.0"
)


APP_ENV = os.getenv("APP_ENV", "development").lower()
ENABLE_DOCUMENT_MANAGEMENT = os.getenv(
    "ENABLE_DOCUMENT_MANAGEMENT",
    "false" if APP_ENV == "production" else "true"
).lower() == "true"

FRONTEND_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,https://ai-customer-calling-agent-ten.vercel.app"
    ).split(",")
    if origin.strip()
]

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    if not ENABLE_DOCUMENT_MANAGEMENT:
        raise HTTPException(status_code=403, detail="Document management is disabled.")

    allowed_extensions = {".pdf", ".txt", ".docx"}

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    safe_filename = Path(file.filename).name
    file_extension = Path(safe_filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT and DOCX files are allowed."
        )

    max_size = 5 * 1024 * 1024
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 5 MB."
        )

    # Validate actual file content
    if file_extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file content."
            )

    elif file_extension == ".txt":
        try:
            text_content = content.decode("utf-8-sig")
            if "\x00" in text_content:
                raise ValueError("Binary content detected.")
        except (UnicodeDecodeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid text file. UTF-8 encoding is required."
            )

    elif file_extension == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as docx_file:
                required_files = {
                    "[Content_Types].xml",
                    "word/document.xml"
                }

                if not required_files.issubset(set(docx_file.namelist())):
                    raise ValueError("Invalid DOCX structure.")

                if sum(item.file_size for item in docx_file.infolist()) > 20 * 1024 * 1024:
                    raise ValueError("DOCX contents are too large.")

        except (zipfile.BadZipFile, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file content."
            )

    documents_dir = (
        BASE_DIR / CONFIG["knowledge_base"] / "documents"
    )
    documents_dir.mkdir(parents=True, exist_ok=True)

    destination = documents_dir / safe_filename

    if destination.exists():
        raise HTTPException(
            status_code=409,
            detail="A document with this filename already exists."
        )

    destination.write_bytes(content)

    try:
        rebuild_index()
    except Exception:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Document processing failed."
        )

    return {
        "message": "Document uploaded and indexed successfully.",
        "filename": safe_filename
    }

@app.get("/documents")
async def list_documents():
    documents_dir = (
        BASE_DIR / CONFIG["knowledge_base"] / "documents"
    )

    if not documents_dir.exists():
        return {"total": 0, "documents": []}

    documents = [
        {
            "filename": file.name,
            "size_bytes": file.stat().st_size
        }
        for file in documents_dir.iterdir()
        if file.is_file()
        and file.suffix.lower() in {".txt", ".pdf", ".docx"}
    ]

    return {
        "total": len(documents),
        "documents": documents
    }

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    if not ENABLE_DOCUMENT_MANAGEMENT:
        raise HTTPException(status_code=403, detail="Document management is disabled.")

    documents_dir = (
        BASE_DIR / CONFIG["knowledge_base"] / "documents"
    )

    safe_filename = Path(filename).name

    if safe_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = documents_dir / safe_filename

    if file_path.suffix.lower() not in {".txt", ".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path.unlink()
    rebuild_index()

    return {
        "message": "Document deleted and knowledge base updated.",
        "filename": safe_filename
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
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
    data = load_business()
    return data.get("sample_orders", [])




def detect_intent(message: str) -> str:
    text = message.lower().strip()

    # 1. Human-agent requests
    human_phrases = [
        "human agent",
        "human assistance",
        "human support",
        "request human",
        "requesting human",
        "provide human assistance",
        "need human assistance",
        "need a human",
        "real person",
        "speak to someone",
        "talk to someone",
        "speak to a human",
        "talk to a human",
        "connect me to an agent",
        "transfer me to an agent",
        "talk to a representative",
        "speak to a representative",
        "live agent",
        "customer representative",
        "customer support agent"
    ]

    if any(term in text for term in human_phrases):
        return "human_agent"

    # 2. Order tracking
    order_phrases = [
        "order status", "track my order",
        "track order", "track my parcel",
        "track parcel", "where is my order",
        "where is my parcel", "order tracking",
        "shipment status", "track shipment",
        "delivery status", "has my order shipped",
        "when will my order arrive",
        "where is my shipment"
    ]

    if (
        re.search(r"\bQC\d{4}\b", message, re.IGNORECASE)
        or any(term in text for term in order_phrases)
    ):
        return "order_status"

    # 3. Business hours
    business_phrases = [
        "business hours", "opening hours",
        "working hours", "open on sunday",
        "closed on sunday", "open on weekends",
        "are you open", "are you closed",
        "what time do you open", "when do you open",
        "when does your store open", "when do you close",
        "what time do you close", "what time are you open",
        "what are your timings", "store timings",
        "shop timings", "what time are you closed",
        "closing time", "opening time"
    ]

    if any(term in text for term in business_phrases):
        return "business_hours"

    return "general_faq"




def get_response(message: str):
    text = message.lower().strip()
    intent = detect_intent(message)

    # 0. Greetings and polite messages
    greetings = {
        "hi", "hello", "hey", "hi there",
        "hello there", "good morning",
        "good afternoon", "good evening"
    }

    if text in greetings:
        return {
            "intent": "greeting",
            "response": (
                "Hello! Welcome to QuickCart. "
                "How can I help you today?"
            ),
            "source": "rule_based"
        }

        # Small talk
    small_talk = {
        "how are you": "I'm doing well! Thanks for asking. How can I help you with QuickCart?",
        "how are you doing": "I'm doing great! How can I assist you today?",
        "what are you doing": "I'm here to help QuickCart customers with orders and store information.",
        "who are you": "I'm QuickCart's AI customer support assistant.",
        "what can you do": "I can help with business hours, order status, and human assistance."
    }

    if text in small_talk:
        return {
            "intent": "general_faq",
            "response": small_talk[text],
            "source": "rule_based"
    }


    if text in {"thanks", "thank you", "thank you so much"}:
        return {
            "intent": "general_faq",
            "response": "You're welcome! Is there anything else I can help you with?",
            "source": "rule_based"
        }

    # 1. Order tracking
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

    # 2. Human escalation
    if intent == "human_agent":
        return {
            "intent": intent,
            "response": (
                "I can register your request for assistance from a human agent. "
                "This demo does not connect to a live agent."
            ),
            "source": "rule_based"
        }

    # 3. Business hours
    if intent == "business_hours":
        business = load_business()

        working_days = {
            day.strip().lower()
            for day in business.get("working_days", [])
        }

        if re.search(r"\bsundays?\b", text) and "sunday" not in working_days:
            response = "We are closed on Sundays."
        else:
            response = business["business_hours"]

        return {
            "intent": intent,
            "response": response,
            "source": "business_configuration"
        }

    # 4. Abuse classification (graceful degradation)
    try:
        message_category = classify_message(message)

        if message_category == "abuse":
            return {
                "intent": "general_faq",
                "response": (
                    "I'm here to help with your QuickCart queries. "
                    "Let's keep our conversation respectful."
                ),
                "source": "local_classifier"
            }

    except Exception as error:
        print(f"Message classification failed: {type(error).__name__}")

    # 5. Retrieve verified information (graceful degradation)
    try:
        results = retrieve_faq(message, top_k=3, threshold=0.45)
    except Exception as error:
        print(f"Knowledge retrieval failed: {type(error).__name__}")
        results = []

    if results:
        best_match = results[0]

        if best_match["source"] == "faq":
            context = (
                f"FAQ question: {best_match['question']}\n"
                f"Verified answer: {best_match['answer']}"
            )
        else:
            context = (
                f"Verified company document: {best_match['source']}\n"
                f"Document information: {best_match['answer']}"
            )

        # 6. Generate AI response
        try:
            ai_result = generate_response(
                question=message,
                context=context,
                ai_settings=AI_SETTINGS
            )

            if ai_result.get("response"):
                return {
                    "intent": best_match["intent"],
                    "response": ai_result["response"],
                    "source": "rag_ai",
                    "knowledge_source": best_match["source"],
                    "provider": ai_result["provider"],
                    "input_tokens": ai_result["input_tokens"],
                    "output_tokens": ai_result["output_tokens"],
                    "matched_question": best_match["question"],
                    "similarity": round(best_match["similarity"], 3)
                }

        except Exception as error:
            print(f"AI generation failed: {type(error).__name__}")

        # 7. Verified answer if AI providers fail
        return {
            "intent": best_match["intent"],
            "response": best_match["answer"],
            "source": "rag_fallback",
            "knowledge_source": best_match["source"],
            "matched_question": best_match["question"],
            "similarity": round(best_match["similarity"], 3)
        }

    # 8. No verified information available
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


    # Save conversation
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
        print(f"Conversation logging error: {error}")

    # Save actual AI API usage
    if result.get("provider"):
        try:
            save_api_usage(
                provider=result["provider"],
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                success=True
            )
        except Exception as error:
            print(f"API usage logging error: {error}")

    return result
