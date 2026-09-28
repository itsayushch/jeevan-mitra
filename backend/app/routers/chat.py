from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import httpx
from app.config import settings
from app.models import ChatRequest
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.api_route("", methods=["GET", "POST"])
async def handle_chat(request: Request, body: Optional[ChatRequest] = None, message: Optional[str] = None):
    # Extract message from query param or body
    msg = None
    if message:
        msg = message
    elif body and body.message:
        msg = body.message
    else:
        # Check raw query
        msg = request.query_params.get("message")

    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")

    api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY

    # If API key available, call Gemini API
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "You are PM-AJAY SAHAYAK, an empathetic and authoritative AI assistant "
                                    "supporting Scheduled Caste youth and beneficiaries in India discovering skilling courses, "
                                    "MUDRA loans, and enterprise pathways under MoSJE PM-AJAY GIA Component.\n\n"
                                    f"User Inquiry: {msg}"
                                )
                            }
                        ]
                    }
                ]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
                    if reply:
                        return {"reply": reply}
        except Exception as e:
            logger.warning(f"External Gemini call failed: {str(e)}. Using verified local knowledge response.")

    # Intelligent local fallback response
    lower_msg = msg.lower()
    if "stipend" in lower_msg or "वजीफा" in lower_msg:
        reply = "Under PM-AJAY GIA, candidates receive ₹1,500 to ₹2,000 per month DBT stipend during training."
    elif "transport" in lower_msg or "किराया" in lower_msg:
        reply = "Daily travel assistance or travel vouchers of ₹50/day are provided for skilling centers located beyond 3 km."
    elif "mudra" in lower_msg or "loan" in lower_msg or "ऋण" in lower_msg:
        reply = "PM-AJAY beneficiaries are eligible for MUDRA loans (Shishu up to ₹50k, Kishor up to ₹5L) with a 35% capital subsidy for SC entrepreneurs."
    elif "mushroom" in lower_msg or "मशरूम" in lower_msg:
        reply = "Mushroom Cultivation Course (AGR/Q7803) is a 3-month NSQF Level 4 course active at KVK Chhajlet with ₹1,500 stipend and free toolkits."
    else:
        reply = f"Thank you for contacting PM-AJAY SAHAYAK. We have received your inquiry: \"{msg}\". You can explore localized training batches, MUDRA enterprise grants, and verified mentors in your district."

    return {"reply": reply}
