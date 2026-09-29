import json
import httpx
from typing import List, Dict, Any
from app.config import settings

class NQRRagService:
    def __init__(self):
        # Mock documents (NQR curriculum data)
        self.documents = [
            {"id": "nqr-001", "course": "Mushroom Cultivation", "content": "The Mushroom Cultivation course covers oyster and button mushroom farming, spawn preparation, climate control, pest management, and post-harvest packaging. Requires Class 8 education. Duration is 200 hours."},
            {"id": "nqr-002", "course": "Solar PV Installation", "content": "Solar PV Installation teaches how to install, test, and commission solar panels for residential and commercial setups. It includes basic electrical wiring and safety. Requires Class 10 education."},
            {"id": "nqr-003", "course": "Retail & Grocery Operations", "content": "Retail operations covers inventory management, customer service, point-of-sale systems, and merchandising. Suitable for self-employment. Requires Class 10 education."},
            {"id": "nqr-004", "course": "Tractor Mechanic", "content": "Tractor Mechanic course teaches engine repair, hydraulic systems, and preventive maintenance of agricultural machinery. Requires Class 8 education and basic physical fitness."}
        ]

    def ask(self, question: str) -> str:
        # Simple exact keyword matching for mock retrieval
        question_lower = question.lower()
        retrieved_docs = []
        for doc in self.documents:
            if doc["course"].lower() in question_lower or any(word in question_lower for word in doc["course"].lower().split()):
                retrieved_docs.append(doc["content"])
        
        if not retrieved_docs:
            retrieved_docs = [doc["content"] for doc in self.documents] # Fallback to all docs if no specific match

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
                
        return "RAG Fallback Answer: Based on the NQR documents, " + " ".join(retrieved_docs)

nqr_rag_service = NQRRagService()
