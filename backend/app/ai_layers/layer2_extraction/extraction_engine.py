from typing import List, Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger
from app.ai_layers.layer2_extraction.validation import SafeProfileExtractionOutput, ExtractedFieldDetail

class ExtractionEngine:
    """
    Extracts structured profile data from conversational interview turns.
    Enforces strict Pydantic validation, rejects hallucinations, bounds confidence,
    and returns clarification questions when confidence is below threshold.
    """

    def __init__(self, threshold: float = settings.CONFIDENCE_THRESHOLD):
        self.threshold = threshold

    def extract_profile(
        self,
        transcript_history: List[Dict[str, str]],
        default_district: str = "Moradabad",
        default_block: str = "Chhajlet"
    ) -> Dict[str, Any]:
        """
        Executes safe extraction pipeline with strict validation and fallback hierarchy.
        """
        user_texts = [turn.get("text", "") for turn in transcript_history if turn.get("speaker") == "user"]
        full_text = " ".join(user_texts).lower()

        # If user hasn't provided input yet, return initial defaults
        if not full_text.strip():
            return SafeProfileExtractionOutput(
                district=default_district,
                block=default_block,
                education="Class 8",
                traditional_or_existing_skills=[],
                interests=[],
                mobility=5.0,
                employment_preference="both",
                confidence_scores={"overall": 0.5},
                clarification_needed="Could you tell us about your background or interests?"
            ).model_dump()

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

        # 2. Education Level & Confidence
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
        elif "graduate" in full_text or "बीए" in full_text or "degree" in full_text:
            edu = "Graduate"
        else:
            edu_conf = 0.60  # Low confidence triggers clarification

        # 3. Interests
        interests = []
        if any(w in full_text for w in ["mushroom", "मशरूम", "farming", "खेती", "फसल"]):
            interests.extend(["Mushroom Cultivation", "Farming"])
        if any(w in full_text for w in ["solar", "सोलर", "बिजली", "electric"]):
            interests.append("Solar PV Installation")
        if any(w in full_text for w in ["sewing", "सिलाई", "कपड़ा", "tailor"]):
            interests.append("Sewing & Apparel")
        if any(w in full_text for w in ["tractor", "ट्रैक्टर", "repair", "रिपेयर", "गाड़ी"]):
            interests.append("Tractor Mechanic & Repair")
        if any(w in full_text for w in ["shop", "दुकान", "retail", "किराना", "बिक्री"]):
            interests.append("Retail & Grocery")

        interest_conf = 0.90 if interests else 0.50
        if not interests:
            interests = ["General Skilling"]

        # 4. Traditional / Existing Skills
        skills = []
        if any(w in full_text for w in ["farming", "किसान", "खेती", "कृषि"]):
            skills.append("Farming")
        if any(w in full_text for w in ["pottery", "मिट्टी", "कुम्हार"]):
            skills.append("Pottery")
        if any(w in full_text for w in ["livestock", "पशु", "डेयरी", "गाय", "भैंस"]):
            skills.append("Livestock Care")
        if any(w in full_text for w in ["electric", "वायरिंग", "बिजली"]):
            skills.append("Basic Wiring")
        if any(w in full_text for w in ["sewing", "सिलाई", "बुनाई"]):
            skills.append("Basic Stitching")

        # 5. Mobility Radius
        radius = 5.0
        mob_conf = 0.90
        if "2 km" in full_text or "2 किमी" in full_text:
            radius = 2.0
        elif "3 km" in full_text or "3 किमी" in full_text:
            radius = 3.0
        elif "10 km" in full_text or "10 किमी" in full_text:
            radius = 10.0
        elif "local" in full_text or "गाँव" in full_text:
            radius = 3.0

        # 6. Work Preference
        pref = "both"
        if any(w in full_text for w in ["self", "खुद", "business", "दुकान", "स्वरोजगार"]):
            pref = "self_employment"
        elif any(w in full_text for w in ["job", "नौकरी", "salary", "वेतन"]):
            pref = "wage"

        # Check if clarification is needed based on low confidence (< 0.70)
        clarification = None
        if edu_conf < self.threshold:
            clarification = "Could you please confirm your highest completed educational standard (Class 5, 8, 10, or 12)?"
        elif interest_conf < self.threshold:
            clarification = "Which trade interests you most: Solar, Sewing, Agriculture, or Vehicle Repair?"

        raw_output = {
            "district": default_district,
            "block": extracted_block,
            "language": "hi" if any(ord(c) > 127 for c in full_text) else "en",
            "education": edu,
            "current_work": "Daily Wage / Farming" if skills else "Unemployed",
            "traditional_or_existing_skills": skills,
            "interests": interests,
            "mobility": radius,
            "access_needs": "None",
            "employment_preference": pref,
            "self_employment_or_wage_preference": pref,
            "confidence_scores": {
                "location": loc_conf,
                "education": edu_conf,
                "interests": interest_conf,
                "mobility": mob_conf
            },
            "clarification_needed": clarification
        }

        # Validate with strict Pydantic model
        validated = SafeProfileExtractionOutput.model_validate(raw_output)
        return validated.model_dump()
