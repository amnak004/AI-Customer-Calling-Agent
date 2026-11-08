
import json
from pathlib import Path

import faiss
import numpy as np
from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]

COMPANY_CONFIG = BASE_DIR / "backend" / "config" / "company.json"

with COMPANY_CONFIG.open("r", encoding="utf-8-sig") as file:
    config = json.load(file)

KNOWLEDGE_BASE = BASE_DIR / config["knowledge_base"]
FAQ_FILE = KNOWLEDGE_BASE / "faqs.json"
DOCUMENTS_DIR = KNOWLEDGE_BASE / "documents"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

knowledge_items = []
index = None


def extract_document_text(file_path):
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8-sig")

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    if suffix == ".docx":
        document = Document(str(file_path))
        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    return ""


def chunk_text(text, chunk_size=500, overlap=80):
    words = text.split()
    chunks = []

    if not words:
        return chunks

    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def load_knowledge_base():
    global knowledge_items, index

    knowledge_items = []

    # Load FAQs
    with FAQ_FILE.open("r", encoding="utf-8-sig") as file:
        faqs = json.load(file)

    for faq in faqs:
        knowledge_items.append({
            "text": faq["question"] + " " + faq["answer"],
            "question": faq["question"],
            "answer": faq["answer"],
            "intent": faq.get("intent", "general_faq"),
            "source": "faq"
        })

    # Load documents
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    supported_extensions = {".pdf", ".txt", ".docx"}

    for file_path in DOCUMENTS_DIR.iterdir():
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in supported_extensions:
            continue

        try:
            text = extract_document_text(file_path)

            for chunk_number, chunk in enumerate(
                chunk_text(text), start=1
            ):
                knowledge_items.append({
                    "text": chunk,
                    "question": "",
                    "answer": chunk,
                    "intent": "general_faq",
                    "source": file_path.name,
                    "chunk": chunk_number
                })

        except Exception as error:
            print(
                f"Could not read {file_path.name}: "
                f"{type(error).__name__}"
            )

    if not knowledge_items:
        index = None
        return

    texts = [
        item["text"] for item in knowledge_items
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    print(
        f"Knowledge base loaded: {len(faqs)} FAQs, "
        f"{len(knowledge_items) - len(faqs)} document chunks."
    )


def retrieve_faq(
    question: str,
    top_k: int = 3,
    threshold: float = 0.45
):
    if index is None:
        return []

    query_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    scores, indices = index.search(
        query_embedding,
        min(top_k, len(knowledge_items))
    )

    results = []

    for score, item_index in zip(scores[0], indices[0]):
        if item_index < 0 or float(score) < threshold:
            continue

        item = knowledge_items[item_index]

        results.append({
            "question": item["question"],
            "answer": item["answer"],
            "intent": item["intent"],
            "similarity": float(score),
            "source": item["source"],
            "chunk": item.get("chunk")
        })

    return results


def rebuild_index():
    load_knowledge_base()


# Build index when the module is imported
load_knowledge_base()
