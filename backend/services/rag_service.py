
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]

COMPANY_CONFIG = BASE_DIR / "backend" / "config" / "company.json"

# Load configuration
with COMPANY_CONFIG.open("r", encoding="utf-8-sig") as file:
    config = json.load(file)

KNOWLEDGE_BASE = BASE_DIR / config["knowledge_base"]
FAQ_FILE = KNOWLEDGE_BASE / "faqs.json"

# Lightweight local embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)

faqs = []
index = None


def load_faqs():
    global faqs, index

    with FAQ_FILE.open("r", encoding="utf-8-sig") as file:
        faqs = json.load(file)

    if not faqs:
        index = None
        return

    questions = [
        item["question"] + " " + item["answer"]
        for item in faqs
    ]

    embeddings = model.encode(
        questions,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)


def retrieve_faq(
    question: str,
    top_k: int = 3,
    threshold: float = 0.35
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
        min(top_k, len(faqs))
    )

    results = []

    for score, faq_index in zip(scores[0], indices[0]):
        if faq_index < 0 or float(score) < threshold:
            continue

        results.append({
            "question": faqs[faq_index]["question"],
            "answer": faqs[faq_index]["answer"],
            "intent": faqs[faq_index].get("intent", "general_faq"),
            "similarity": float(score)
        })

    return results



# Build index once when this module is imported
load_faqs()
