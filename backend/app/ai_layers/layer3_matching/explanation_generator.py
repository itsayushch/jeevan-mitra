from typing import Dict, Any, Optional

class ExplanationGenerator:
    """Generates explainable rationale, audio script, tradeoffs, and skill gaps for recommendations."""

    @staticmethod
    def generate(
        qual: Dict[str, Any],
        best_opp: Optional[Dict[str, Any]],
        interests: list,
        match_state: str,
        lang: str = "hi"
    ) -> Dict[str, str]:
        title = qual.get("title", "")
        sector = qual.get("sector", "")
        duration = qual.get("duration_hours", 200)

        if match_state == "Verified Match" and best_opp:
            centre = best_opp.get("centre_or_employer_name", "Local Training Centre")
            dist = best_opp.get("distance_km", 4.2)
            stipend = best_opp.get("stipend_amount_inr", 1500)

            if lang == "hi":
                text = f"यह कोर्स आपके रुचियों और पृष्ठभूमि से मेल खाता है। {centre} में {dist} किमी दूरी पर आगामी बैच सत्यापित है (वजीफा: ₹{stipend}/माह)।"
                audio = f"हमने आपके लिए {title} चुना है। आपके नजदीक {centre} पर इसकी सीट उपलब्ध है।"
                tradeoff = f"{duration} घंटे का प्रशिक्षण। दैनिक उपस्थिति आवश्यक है।"
                gaps = "बुनियादी उपकरण संचालन और सुरक्षा प्रोटोकॉल सीखने होंगे।"
            else:
                text = f"Matches your interest in {sector}. Confirmed active batch at {centre} ({dist} km away) with ₹{stipend}/mo stipend."
                audio = f"We found a verified seat for {title} at {centre} within your travel limit."
                tradeoff = f"{duration} hours intensive course requiring daily attendance."
                gaps = "Requires mastering safety protocols and hands-on tools."
        else:
            if lang == "hi":
                text = f"यह राष्ट्रीय योग्यता ({title}) आपकी रुचि से मेल खाती है, लेकिन वर्तमान में आपके 5 किमी क्षेत्र में सक्रिय बैच की पुष्टि नहीं हुई है।"
                audio = f"{title} आपके लिए उपयुक्त है, लेकिन स्थानीय बैच की जांच फील्ड वर्कर करेंगे।"
                tradeoff = "निकटतम केंद्र 15 किमी से अधिक दूर हो सकता है। मोबाइल यूनिट की प्रतीक्षा करें।"
                gaps = "प्रारंभिक व्यावसायिक शब्दावली और बुनियादी गणना।"
            else:
                text = f"High NQR qualification match for {title}, but no live batch is currently verified within your immediate radius."
                audio = f"{title} matches your profile, but local batch availability must be verified by a worker."
                tradeoff = "Nearest center might require extended travel unless mobile unit is deployed."
                gaps = "Foundational arithmetic and equipment familiarity."

        return {
            "explanation_text": text,
            "audio_explanation_script": audio,
            "tradeoff_summary": tradeoff,
            "skill_gap_summary": gaps
        }
