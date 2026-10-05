import json
import httpx
from typing import List, Dict, Any
from app.config import settings

class NQRRagService:
    def __init__(self):
        pass

    @property
    def documents(self):
        from app.services.nqr_catalogue import load_snapshot
        from datetime import date
        snapshot = load_snapshot()
        return [{"id": str(item["record_id"]), "course": item["title"],
                 "content": json.dumps({**item, "source_checked_at": snapshot["checked_at"],
                                        "local_batch": "Not verified; NQR is a qualification register."}, ensure_ascii=False)}
                for item in snapshot["records"] if item["valid_to"] >= date.today().isoformat()]

    def ask(self, question: str) -> str:
        # Simple exact keyword matching for mock retrieval
        question_lower = question.lower()
        documents = self.documents
        if not documents:
            return "No current NQR course information is available. Please ask a helper."
        retrieved_docs = []
        for doc in documents:
            if doc["course"].lower() in question_lower or any(word in question_lower for word in doc["course"].lower().split()):
                retrieved_docs.append(doc["content"])

        if not retrieved_docs:
            retrieved_docs = [doc["content"] for doc in documents]

        context = "\n".join(retrieved_docs)

        # Call Gemini or Groq to synthesize the answer
        gemini_key = settings.GEMINI_API_KEY or settings.AI_API_KEY

        if (settings.AI_PROVIDER == 'gemini' or not settings.AI_PROVIDER) and gemini_key:
            try:
                response = httpx.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent',
                    headers={'x-goog-api-key': gemini_key},
                    timeout=20,
                    json={
                        "systemInstruction": {"parts": [{"text": "You are a helpful career counselor. Answer the user's question based strictly on the provided National Qualification Register (NQR) document context. Do not invent details."}]},
                        "contents": [
                            {"role": "user", "parts": [{"text": f"Context:\n{context}\n\nQuestion: {question}"}]}
                        ],
                        "generationConfig": {"temperature": 0.1}
                    }
                )
                response.raise_for_status()
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                pass

        if settings.GROQ_API_KEY:
            try:
                response = httpx.post(
                    'https://api.groq.com/openai/v1/chat/completions',
                    headers={'Authorization': f'Bearer {settings.GROQ_API_KEY}', 'Content-Type': 'application/json'},
                    timeout=20,
                    json={
                        'model': settings.GROQ_MODEL,
                        'messages': [
                            {'role': 'system', 'content': "You are a helpful career counselor. Answer the user's question based strictly on the provided National Qualification Register (NQR) document context. Do not invent details."},
                            {'role': 'user', 'content': f"Context:\n{context}\n\nQuestion: {question}"}
                        ],
                        'temperature': 0.1
                    }
                )
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except Exception as e:
                pass

        return "Official NQR information: " + " ".join(retrieved_docs)

nqr_rag_service = NQRRagService()
