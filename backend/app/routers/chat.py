from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import httpx
from app.config import settings
from app.models import ChatRequest
from app.utils.logger import logger
from app.schemas.locale import resolve_locale, SupportedLocale

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.api_route("", methods=["GET", "POST"])
async def handle_chat(request: Request, body: Optional[ChatRequest] = None, message: Optional[str] = None):
    # Extract message from query param or body
    msg = None
    explicit_lang = None
    if message:
        msg = message
    elif body and body.message:
        msg = body.message
        explicit_lang = body.language
    else:
        msg = request.query_params.get("message")
        explicit_lang = request.query_params.get("language")

    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")

    resolved_locale = resolve_locale(
        request=request,
        explicit_locale=explicit_lang,
        require_enabled=True
    )
    lang_code = resolved_locale.value

    api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY

    # If API key available, call Gemini API
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            instruction = (
                f"You are PM-AJAY SAHAYAK, an empathetic and authoritative AI assistant "
                f"supporting Scheduled Caste youth and beneficiaries in India discovering skilling courses, "
                f"MUDRA loans, and enterprise pathways under MoSJE PM-AJAY GIA Component.\n"
                f"Respond only in the requested supported language: {lang_code}.\n"
                f"Use simple, respectful wording suitable for the beneficiary.\n"
                f"Do not translate proper names, qualification IDs, official programme labels, or verified data fields inaccurately.\n"
                f"If a precise term has no translation, retain the term and explain simply.\n\n"
                f"User Inquiry: {msg}"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": instruction
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
                        return {"reply": reply, "locale": lang_code}
        except Exception as e:
            logger.warning(f"External Gemini call failed: {str(e)}. Using verified local knowledge response.")

    # Intelligent local fallback response based on resolved locale
    lower_msg = msg.lower()
    is_hi = (lang_code == "hi")

    if "stipend" in lower_msg or "वजीफा" in lower_msg:
        reply = (
            "पीएम-अजय (PM-AJAY) सहायता अनुदान के तहत, उम्मीदवारों को प्रशिक्षण के दौरान प्रति माह ₹1,500 से ₹2,000 डीबीटी (DBT) वजीफा प्राप्त होता है।"
            if is_hi
            else "Under PM-AJAY GIA, candidates receive ₹1,500 to ₹2,000 per month DBT stipend during training."
        )
    elif "transport" in lower_msg or "किराया" in lower_msg or "यात्रा" in lower_msg:
        reply = (
            "3 किमी से अधिक दूरी पर स्थित कौशल केंद्रों के लिए दैनिक यात्रा सहायता या ₹50/दिन के यात्रा वाउचर प्रदान किए जाते हैं।"
            if is_hi
            else "Daily travel assistance or travel vouchers of ₹50/day are provided for skilling centers located beyond 3 km."
        )
    elif "mudra" in lower_msg or "loan" in lower_msg or "ऋण" in lower_msg:
        reply = (
            "पीएम-अजय लाभार्थी अनुसूचित जाति के उद्यमियों के लिए 35% पूंजीगत सब्सिडी के साथ मुद्रा ऋण (शिशु ₹50,000 तक, किशोर ₹5 लाख तक) के पात्र हैं।"
            if is_hi
            else "PM-AJAY beneficiaries are eligible for MUDRA loans (Shishu up to ₹50k, Kishor up to ₹5L) with a 35% capital subsidy for SC entrepreneurs."
        )
    elif "mushroom" in lower_msg or "मशरूम" in lower_msg:
        reply = (
            "मशरूम की खेती का पाठ्यक्रम (AGR/Q7803) केवीके छजलैट में ₹1,500 वजीफा और मुफ्त टूलकिट के साथ सक्रिय 3 महीने का एनएसक्यूएफ स्तर 4 पाठ्यक्रम है।"
            if is_hi
            else "Mushroom Cultivation Course (AGR/Q7803) is a 3-month NSQF Level 4 course active at KVK Chhajlet with ₹1,500 stipend and free toolkits."
        )
    else:
        reply = (
            f"पीएम-अजय सहायक से संपर्क करने के लिए धन्यवाद। हमें आपका प्रश्न प्राप्त हुआ है: \"{msg}\"। आप अपने जिले में स्थानीय प्रशिक्षण बैच, मुद्रा उद्यम अनुदान और सत्यापित मार्गदर्शकों की जानकारी प्राप्त कर सकते हैं।"
            if is_hi
            else f"Thank you for contacting PM-AJAY SAHAYAK. We have received your inquiry: \"{msg}\". You can explore localized training batches, MUDRA enterprise grants, and verified mentors in your district."
        )

    return {"reply": reply, "locale": lang_code}
