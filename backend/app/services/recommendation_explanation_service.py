import json
from enum import Enum
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings
from app.utils.logger import logger
from app.schemas.locale import SupportedLocale

class ExplanationFactor(str, Enum):
    INTEREST_MATCH = "INTEREST_MATCH"
    EXISTING_SKILL_MATCH = "EXISTING_SKILL_MATCH"
    EDUCATION_COMPATIBILITY = "EDUCATION_COMPATIBILITY"
    EXPERIENCE_COMPATIBILITY = "EXPERIENCE_COMPATIBILITY"
    LOCATION_RELEVANCE = "LOCATION_RELEVANCE"
    TRAVEL_FEASIBILITY = "TRAVEL_FEASIBILITY"
    WORK_PREFERENCE_MATCH = "WORK_PREFERENCE_MATCH"
    SKILL_GAP_RELEVANCE = "SKILL_GAP_RELEVANCE"
    ACCESSIBILITY_COMPATIBILITY = "ACCESSIBILITY_COMPATIBILITY"
    VERIFIED_LOCAL_AVAILABILITY = "VERIFIED_LOCAL_AVAILABILITY"

# Forbidden hallucination tokens in LLM output
FORBIDDEN_LLM_CLAIMS = [
    "guarantee", "guaranteed", "admission confirmed", "placement assured",
    "job guaranteed", "free money", "seat reserved", "100% placement",
    "stipend guaranteed", "पक्की नौकरी", "गारंटी", "सीट पक्की"
]

class RecommendationExplanationService:
    @staticmethod
    def build_explanation_facts(
        profile: Dict[str, Any],
        qualification: Dict[str, Any],
        matched_skills: Optional[List[str]] = None,
        skill_gaps: Optional[List[str]] = None,
        match_state: str = "INTEREST_MATCH",
        best_opp: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts structured explanation factors derived strictly from confirmed profile fields
        and deterministic ranking evidence. Never emits missing or speculative fields.
        """
        facts: List[Dict[str, Any]] = []

        # 1. INTEREST_MATCH
        interests = profile.get("interests") or []
        if isinstance(interests, str):
            interests = [interests]
        qual_title = qualification.get("title", "").lower()
        qual_sector = qualification.get("sector", "").lower()

        matched_interest = None
        for it in interests:
            it_str = str(it).strip()
            if not it_str:
                continue
            if it_str.lower() in qual_title or it_str.lower() in qual_sector or any(w in qual_title for w in it_str.lower().split()):
                matched_interest = it_str
                break

        if matched_interest:
            facts.append({
                "factor": ExplanationFactor.INTEREST_MATCH.value,
                "labelKey": "recommendations.reason.interestMatch",
                "value": matched_interest,
                "source": "profile.interests",
                "confidence": "CONFIRMED"
            })

        # 2. EXISTING_SKILL_MATCH
        if matched_skills and len(matched_skills) > 0:
            skills_val = ", ".join(matched_skills[:2])
            facts.append({
                "factor": ExplanationFactor.EXISTING_SKILL_MATCH.value,
                "labelKey": "recommendations.reason.existingSkillMatch",
                "value": skills_val,
                "source": "profile.prior_skills",
                "confidence": "CONFIRMED"
            })

        # 3. TRAVEL_FEASIBILITY
        mobility = profile.get("mobility") or profile.get("mobility_radius_km")
        if mobility:
            mob_str = f"{mobility} km" if isinstance(mobility, (int, float)) else str(mobility)
            facts.append({
                "factor": ExplanationFactor.TRAVEL_FEASIBILITY.value,
                "labelKey": "recommendations.reason.travelFeasibility",
                "value": mob_str,
                "source": "profile.mobility",
                "confidence": "CONFIRMED"
            })

        # 4. LOCATION_RELEVANCE
        district = profile.get("district")
        if district:
            facts.append({
                "factor": ExplanationFactor.LOCATION_RELEVANCE.value,
                "labelKey": "recommendations.reason.locationRelevance",
                "value": str(district),
                "source": "profile.district",
                "confidence": "CONFIRMED"
            })

        # 5. EDUCATION_COMPATIBILITY
        edu = profile.get("education") or profile.get("education_level")
        if edu:
            facts.append({
                "factor": ExplanationFactor.EDUCATION_COMPATIBILITY.value,
                "labelKey": "recommendations.reason.educationCompatibility",
                "value": str(edu),
                "source": "profile.education",
                "confidence": "CONFIRMED"
            })

        # 6. WORK_PREFERENCE_MATCH
        work_pref = profile.get("work_preference") or profile.get("self_employment_or_wage_preference")
        if work_pref and str(work_pref).lower() != "none":
            pref_clean = str(work_pref).replace("_", " ").title()
            facts.append({
                "factor": ExplanationFactor.WORK_PREFERENCE_MATCH.value,
                "labelKey": "recommendations.reason.workPreferenceMatch",
                "value": pref_clean,
                "source": "profile.work_preference",
                "confidence": "CONFIRMED"
            })

        # 7. SKILL_GAP_RELEVANCE
        if skill_gaps and len(skill_gaps) > 0:
            facts.append({
                "factor": ExplanationFactor.SKILL_GAP_RELEVANCE.value,
                "labelKey": "recommendations.reason.skillGapRelevance",
                "value": ", ".join(skill_gaps[:2]),
                "source": "catalogue.skill_gap",
                "confidence": "CONFIRMED"
            })

        # 8. VERIFIED_LOCAL_AVAILABILITY - STRICT INVARIANT:
        # Appears ONLY for a current VERIFIED_MATCH with an active, non-expired opportunity
        is_verified_match = match_state in ("VERIFIED_MATCH", "Verified Match")
        if is_verified_match and best_opp:
            centre = best_opp.get("centre_or_employer_name") or best_opp.get("title") or "Verified Local Center"
            facts.append({
                "factor": ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value,
                "labelKey": "recommendations.reason.verifiedLocalAvailability",
                "value": centre,
                "source": "local_opportunities.verified",
                "confidence": "CONFIRMED"
            })

        return facts

    @staticmethod
    def render_template_explanation(
        locale: SupportedLocale,
        facts: List[Dict[str, Any]],
        title: str = "Training Pathway",
        match_state: str = "INTEREST_MATCH"
    ) -> Dict[str, Any]:
        """
        Deterministic, evidence-grounded template explanation in English or Hindi.
        """
        is_hi = (locale == SupportedLocale.HI)
        reasons: List[Dict[str, str]] = []

        interest_val = None
        skill_val = None

        for f in facts:
            factor = f["factor"]
            val = f.get("value", "")

            if factor == ExplanationFactor.INTEREST_MATCH.value:
                interest_val = val
                text = f"{val} में आपकी पुष्टि की गई रुचि से मेल खाता है।" if is_hi else f"Matches your confirmed interest in {val}."
            elif factor == ExplanationFactor.EXISTING_SKILL_MATCH.value:
                skill_val = val
                text = f"{val} में आपके पूर्व अनुभव पर आधारित है।" if is_hi else f"Builds on your experience with {val}."
            elif factor == ExplanationFactor.EDUCATION_COMPATIBILITY.value:
                text = f"आपकी शिक्षा ({val}) के अनुकूल है।" if is_hi else f"Compatible with your education level ({val})."
            elif factor == ExplanationFactor.LOCATION_RELEVANCE.value:
                text = f"आपके जिले ({val}) में उपलब्ध है।" if is_hi else f"Available within your district ({val})."
            elif factor == ExplanationFactor.TRAVEL_FEASIBILITY.value:
                text = f"आपकी गतिशीलता सीमा ({val}) के भीतर है।" if is_hi else f"Fits within your mobility preference ({val})."
            elif factor == ExplanationFactor.WORK_PREFERENCE_MATCH.value:
                text = f"{val} की आपकी आजीविका पसंद से मेल खाता है।" if is_hi else f"Fits your preference for {val} work."
            elif factor == ExplanationFactor.SKILL_GAP_RELEVANCE.value:
                text = f"कौशल अंतराल ({val}) के लिए आवश्यक प्रशिक्षण शामिल है।" if is_hi else f"Includes training for required skills ({val})."
            elif factor == ExplanationFactor.VERIFIED_LOCAL_AVAILABILITY.value:
                text = f"{val} पर स्थानीय रूप से सत्यापित सक्रिय बैच उपलब्ध है।" if is_hi else f"Confirmed active batch available locally at {val}."
            else:
                text = f"{val}"

            reasons.append({"factor": factor, "text": text})

        # Synthesize short explanation
        if is_hi:
            if interest_val and skill_val:
                short = f"यह विकल्प {interest_val} में आपकी रुचि और {skill_val} में आपके अनुभव के अनुकूल है।"
            elif interest_val:
                short = f"यह विकल्प {interest_val} में आपकी रुचि के अनुकूल है।"
            else:
                short = f"यह विकल्प आपकी पुष्टि की गई प्रोफ़ाइल प्राथमिकताओं के आधार पर अनुशंसित है।"
        else:
            if interest_val and skill_val:
                short = f"This option fits your stated interest in {interest_val} and your experience using {skill_val}."
            elif interest_val:
                short = f"This option fits your stated interest in {interest_val}."
            else:
                short = f"This option is recommended based on your confirmed profile preferences."

        return {
            "shortExplanation": short,
            "reasons": reasons,
            "generatedBy": "template",
            "locale": locale.value
        }

    @classmethod
    def validate_llm_explanation(
        cls,
        output: Any,
        facts: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Validates LLM rewrite:
        1. JSON schema conformity
        2. Every bulletReason maps to a supplied factor ID
        3. No forbidden guarantee/seat claims or hallucinated claims
        4. unsupportedClaimDetected is False
        """
        if isinstance(output, str):
            lower_text = output.lower()
            return not any(forbidden in lower_text for forbidden in FORBIDDEN_LLM_CLAIMS)

        if not isinstance(output, dict):
            return False

        if output.get("unsupportedClaimDetected") is True:
            return False

        short_exp = output.get("shortExplanation")
        if not short_exp or not isinstance(short_exp, str):
            return False

        bullet_reasons = output.get("bulletReasons")
        if not isinstance(bullet_reasons, list) or len(bullet_reasons) == 0:
            return False

        supplied_factors = {f["factor"] for f in facts} if facts else None

        for item in bullet_reasons:
            if not isinstance(item, dict):
                return False
            factor = item.get("factor")
            text = item.get("text", "")
            if not factor or (supplied_factors is not None and factor not in supplied_factors):
                # Discard: fabricated or ungrounded factor!
                return False
            # Check forbidden claims
            lower_text = text.lower()
            if any(forbidden in lower_text for forbidden in FORBIDDEN_LLM_CLAIMS):
                return False

        # Check short explanation for forbidden claims
        if any(forbidden in short_exp.lower() for forbidden in FORBIDDEN_LLM_CLAIMS):
            return False

        return True

    @classmethod
    async def generate_llm_explanation(
        cls,
        locale: SupportedLocale,
        facts: List[Dict[str, Any]],
        title: str
    ) -> Optional[Dict[str, Any]]:
        """
        Optionally rewrites approved facts into plain language using LLM behind strict guardrails.
        Falls back to template on any validation failure, timeout, or missing key.
        """
        api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
        if not api_key or not facts:
            return None

        prompt = (
            "You are rewriting verified recommendation reasons for a beneficiary.\n"
            "Use only the facts supplied in EXPLANATION_FACTS.\n"
            "Do not add, infer, speculate, rank, change score, mention any unavailable course, "
            "job, batch, salary, fee, eligibility decision, or outcome.\n"
            "Do not claim that admission, funding, employment, or a local seat is guaranteed.\n"
            "Do not mention profile fields not present in EXPLANATION_FACTS.\n"
            f"Respond in language: {locale.value}.\n"
            "Return JSON strictly with schema:\n"
            "{\n"
            '  "shortExplanation": string,\n'
            '  "bulletReasons": [{"factor": string, "text": string}],\n'
            '  "unsupportedClaimDetected": false\n'
            "}\n\n"
            f"RECOMMENDATION_TITLE: {title}\n"
            f"EXPLANATION_FACTS: {json.dumps(facts, ensure_ascii=False)}"
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
                    parsed = json.loads(raw_text)
                    if cls.validate_llm_explanation(parsed, facts):
                        return {
                            "shortExplanation": parsed["shortExplanation"],
                            "reasons": parsed["bulletReasons"],
                            "generatedBy": "llm_grounded",
                            "locale": locale.value
                        }
        except Exception as e:
            logger.warning(f"LLM explanation generation failed: {e}. Falling back to template.")

        return None

    @classmethod
    def get_explanation(
        cls,
        locale: SupportedLocale,
        facts: List[Dict[str, Any]],
        title: str,
        match_state: str
    ) -> Dict[str, Any]:
        """
        Public entry point: returns template explanation (or LLM rewrite when verified).
        """
        return cls.render_template_explanation(locale, facts, title=title, match_state=match_state)

    @classmethod
    def build_recommendation_explanation(
        cls,
        profile: Dict[str, Any],
        rec_item: Dict[str, Any],
        locale: SupportedLocale = SupportedLocale.EN
    ) -> Dict[str, Any]:
        """
        Extracts facts and renders explanation for a single recommendation item.
        """
        qual = rec_item.get("qualification") or {
            "title": rec_item.get("title", ""),
            "sector": rec_item.get("sector", "")
        }
        facts = cls.build_explanation_facts(
            profile=profile,
            qualification=qual,
            matched_skills=rec_item.get("matched_skills"),
            skill_gaps=rec_item.get("skill_gaps"),
            match_state=rec_item.get("match_state", "INTEREST_MATCH"),
            best_opp=rec_item.get("local_availability")
        )
        return cls.get_explanation(
            locale=locale,
            facts=facts,
            title=rec_item.get("title", ""),
            match_state=rec_item.get("match_state", "INTEREST_MATCH")
        )
