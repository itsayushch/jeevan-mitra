from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger

class ExtractionEngine:
    """Extracts structured profile JSON from raw conversation transcripts."""

    def __init__(self, threshold: float = settings.CONFIDENCE_THRESHOLD):
        self.threshold = threshold

    def extract_profile(
        self,
        transcript_history: List[Dict[str, str]],
        default_district: str = "Moradabad",
        default_block: str = "Chhajlet"
    ) -> Dict[str, Any]:
        full_text = " ".join([turn.get("text", "") for turn in transcript_history]).lower()

        # 1. Location / Block Extraction
        extracted_block = default_block
        loc_conf = 0.85
        if "chhajlet" in full_text or "छजलैट" in full_text:
            extracted_block = "Chhajlet"
            loc_conf = 0.95
        elif "bahjoi" in full_text or "बहजोई" in full_text:
            extracted_block = "Bahjoi"
            loc_conf = 0.95
        elif "bilari" in full_text or "बिलारी" in full_text:
            extracted_block = "Bilari"
            loc_conf = 0.95
        elif "kundarki" in full_text or "कुंदरकी" in full_text:
            extracted_block = "Kundarki"
            loc_conf = 0.95

        # 2. Education Level
        edu = "Class 10"
        edu_conf = 0.90
        if "12" in full_text or "बारह" in full_text or "inter" in full_text:
            edu = "Class 12"
        elif "10" in full_text or "दस" in full_text or "matric" in full_text:
            edu = "Class 10"
        elif "8" in full_text or "आठ" in full_text:
            edu = "Class 8"
        elif "5" in full_text or "पांच" in full_text:
            edu = "Class 5"
        elif "graduate" in full_text or "बीए" in full_text:
            edu = "Graduate"

        # 3. Interests
        interests = []
        if any(w in full_text for w in ["mushroom", "मशरूम", "farming", "खेती", "फसल"]):
            interests.append("Mushroom Cultivation")
            interests.append("Farming")
        if any(w in full_text for w in ["solar", "सोलर", "बिजली", "electric"]):
            interests.append("Solar PV Installation")
        if any(w in full_text for w in ["sewing", "सिलाई", "कपड़ा", "tailor"]):
            interests.append("Sewing & Apparel")
        if any(w in full_text for w in ["tractor", "ट्रैक्टर", "repair", "रिपेयर", "गाड़ी"]):
            interests.append("Tractor Mechanic & Repair")
        if any(w in full_text for w in ["shop", "दुकान", "retail", "किराना", "बिक्री"]):
            interests.append("Retail & Grocery")

        if not interests:
            interests = ["Mushroom Cultivation", "Farming", "Agri-Business"]

        # 4. Family Trades
        family_trades = []
        if any(w in full_text for w in ["farming", "किसान", "खेती", "कृषि"]):
            family_trades.append("Farming")
        if any(w in full_text for w in ["pottery", "मिट्टी", "कुम्हार"]):
            family_trades.append("Pottery")
        if any(w in full_text for w in ["livestock", "पशु", "डेयरी"]):
            family_trades.append("Livestock")
        if not family_trades:
            family_trades = ["Farming", "Pottery"]

        # 5. Mobility Radius
        radius = 5.0
        if "2 km" in full_text or "2 किमी" in full_text:
            radius = 2.0
        elif "3 km" in full_text or "3 किमी" in full_text:
            radius = 3.0
        elif "10 km" in full_text or "10 किमी" in full_text:
            radius = 10.0

        # 6. Work Preference
        pref = "both"
        if any(w in full_text for w in ["self", "खुद", "business", "दुकान", "स्वरोजगार"]):
            pref = "self_employment"
        elif any(w in full_text for w in ["job", "नौकरी", "salary", "वेतन"]):
            pref = "wage"

        return {
            "district": default_district,
            "block": extracted_block,
            "education_level": edu,
            "interests": interests,
            "skills": interests,
            "family_trades": family_trades,
            "mobility_radius_km": radius,
            "accessibility_needs": "None",
            "work_preference": pref,
            "confidence_scores": {
                "location": loc_conf,
                "education": edu_conf,
                "interests": 0.88,
                "mobility": 0.90
            }
        }
