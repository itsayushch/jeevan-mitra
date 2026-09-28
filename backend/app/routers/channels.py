from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/channels", tags=["Channels"])

class ChannelMessage(BaseModel):
    sender: str
    message: str
    channel: str = "ivr"

@router.post("/ivr/webhook")
def ivr_webhook(data: ChannelMessage):
    return {
        "status": "received",
        "channel": "ivr",
        "twiml_response": f"<Response><Say>Namaste. JeevanMitra received your call from {data.sender}.</Say></Response>"
    }

@router.post("/whatsapp/webhook")
def whatsapp_webhook(data: ChannelMessage):
    return {
        "status": "received",
        "channel": "whatsapp",
        "reply": f"Namaste! JeevanMitra AI Sahayak received: '{data.message}'."
    }
