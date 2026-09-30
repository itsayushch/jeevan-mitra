from typing import Dict, Set, List, Optional

class ReferralStateMachine:
    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        "DRAFT": {"READY_TO_SEND", "CANCELLED"},
        "READY_TO_SEND": {"REFERRED", "CANCELLED", "OPPORTUNITY_CLOSED", "BENEFICIARY_DECLINED"},
        "REFERRED": {
            "CONTACTED", "DOCUMENTS_PENDING", "ELIGIBILITY_REVIEW",
            "BENEFICIARY_DECLINED", "LOST_TO_FOLLOW_UP", "OPPORTUNITY_CLOSED", "CANCELLED"
        },
        "CONTACTED": {
            "DOCUMENTS_PENDING", "ELIGIBILITY_REVIEW", "ENROLLED",
            "BENEFICIARY_DECLINED", "LOST_TO_FOLLOW_UP", "OPPORTUNITY_CLOSED"
        },
        "DOCUMENTS_PENDING": {
            "ELIGIBILITY_REVIEW", "ENROLLED", "NOT_ELIGIBLE",
            "BENEFICIARY_DECLINED", "LOST_TO_FOLLOW_UP", "OPPORTUNITY_CLOSED"
        },
        "ELIGIBILITY_REVIEW": {
            "ENROLLED", "NOT_ELIGIBLE", "DOCUMENTS_PENDING",
            "BENEFICIARY_DECLINED", "OPPORTUNITY_CLOSED"
        },
        "ENROLLED": {
            "TRAINING_STARTED", "BENEFICIARY_DECLINED", "LOST_TO_FOLLOW_UP", "OPPORTUNITY_CLOSED"
        },
        "TRAINING_STARTED": {
            "COMPLETED", "LOST_TO_FOLLOW_UP", "CANCELLED"
        },
        "COMPLETED": {
            "EMPLOYED", "SELF_EMPLOYED", "CLOSED"
        },
        "EMPLOYED": {"CLOSED"},
        "SELF_EMPLOYED": {"CLOSED"},
        "CLOSED": set(),
        "CANCELLED": set(),
        "BENEFICIARY_DECLINED": set(),
        "NOT_ELIGIBLE": set(),
        "LOST_TO_FOLLOW_UP": set(),
        "OPPORTUNITY_CLOSED": set(),
    }

    TERMINAL_STATUSES: Set[str] = {
        "CLOSED", "CANCELLED", "BENEFICIARY_DECLINED", "NOT_ELIGIBLE", "LOST_TO_FOLLOW_UP", "OPPORTUNITY_CLOSED"
    }

    BENEFICIARY_DISPLAY_MAP: Dict[str, Dict[str, str]] = {
        "DRAFT": {
            "display": "Preparing Referral",
            "next_step": "A field worker is preparing your referral details.",
            "display_hi": "सिफारिश तैयार हो रही है",
            "next_step_hi": "फील्ड वर्कर आपके विवरण की समीक्षा कर रहे हैं।"
        },
        "READY_TO_SEND": {
            "display": "Ready for Submission",
            "next_step": "Your referral is ready and waiting for dispatch.",
            "display_hi": "भेजने के लिए तैयार",
            "next_step_hi": "आपकी सिफारिश केंद्र को भेजने के लिए तैयार है।"
        },
        "REFERRED": {
            "display": "Referral Submitted",
            "next_step": "Your referral has been sent to the training centre.",
            "display_hi": "सिफारिश भेजी गई",
            "next_step_hi": "आपकी सिफारिश प्रशिक्षण केंद्र को भेज दी गई है।"
        },
        "CONTACTED": {
            "display": "Contact Initiated",
            "next_step": "The training centre or field worker has initiated contact.",
            "display_hi": "संपर्क स्थापित हुआ",
            "next_step_hi": "प्रशिक्षण केंद्र या कार्यकर्ता ने आपसे संपर्क किया है।"
        },
        "DOCUMENTS_PENDING": {
            "display": "Information Needed",
            "next_step": "A field worker will contact you regarding required details.",
            "display_hi": "दस्तावेज़ लंबित",
            "next_step_hi": "फील्ड कार्यकर्ता आवश्यक जानकारी के लिए आपसे संपर्क करेंगे।"
        },
        "ELIGIBILITY_REVIEW": {
            "display": "Under Review",
            "next_step": "Your admission eligibility is currently being verified.",
            "display_hi": "समीक्षाधीन",
            "next_step_hi": "आपकी प्रवेश पात्रता की पुष्टि की जा रही है।"
        },
        "ENROLLED": {
            "display": "Enrolment Confirmed",
            "next_step": "You are enrolled in the training batch.",
            "display_hi": "नामांकन पक्का हुआ",
            "next_step_hi": "प्रशिक्षण बैच में आपका प्रवेश सुनिश्चित हो गया है।"
        },
        "TRAINING_STARTED": {
            "display": "Training Underway",
            "next_step": "Attend regular sessions at the designated centre.",
            "display_hi": "प्रशिक्षण शुरू",
            "next_step_hi": "प्रशिक्षण केंद्र में कक्षाएं शुरू हो चुकी हैं।"
        },
        "COMPLETED": {
            "display": "Training Completed",
            "next_step": "Certification earned. Connecting with placement options.",
            "display_hi": "प्रशिक्षण पूर्ण",
            "next_step_hi": "प्रशिक्षण सफलतापूर्वक पूरा हुआ। आजीविका विकल्पों से जोड़ा जा रहा है।"
        },
        "EMPLOYED": {
            "display": "Employed",
            "next_step": "Wage employment verified.",
            "display_hi": "रोजगार प्राप्त",
            "next_step_hi": "वेतनभोगी रोजगार सत्यापित हुआ।"
        },
        "SELF_EMPLOYED": {
            "display": "Self-Employed",
            "next_step": "Micro-enterprise/self-employment initiated.",
            "display_hi": "स्वरोजगार सक्रिय",
            "next_step_hi": "स्वरोजगार / सूक्ष्म उद्यम शुरू हो चुका है।"
        },
        "CLOSED": {
            "display": "Case Completed",
            "next_step": "All steps completed successfully.",
            "display_hi": "मामला संपन्न",
            "next_step_hi": "सभी प्रक्रियाएं पूरी हो चुकी हैं।"
        },
        "CANCELLED": {
            "display": "Referral Cancelled",
            "next_step": "This referral was cancelled.",
            "display_hi": "सिफारिश रद्द",
            "next_step_hi": "यह सिफारिश रद्द कर दी गई है।"
        },
        "BENEFICIARY_DECLINED": {
            "display": "Declined by Candidate",
            "next_step": "You opted out of this batch. Ask worker for alternates.",
            "display_hi": "उम्मीदवार द्वारा अस्वीकृत",
            "next_step_hi": "आपने इस अवसर से बाहर रहने का विकल्प चुना।"
        },
        "NOT_ELIGIBLE": {
            "display": "Criteria Not Met",
            "next_step": "Admission criteria not met. Worker will assist with alternatives.",
            "display_hi": "पात्रता नहीं मिली",
            "next_step_hi": "इस बैच की शर्तें पूरी नहीं हुईं। अन्य विकल्पों के लिए कार्यकर्ता से पूछें।"
        },
        "OPPORTUNITY_CLOSED": {
            "display": "Batch Unavailable",
            "next_step": "Batch has filled up or closed. Our team will find other options.",
            "display_hi": "बैच उपलब्ध नहीं",
            "next_step_hi": "यह बैच भर चुका है या बंद हो गया है। नई संभावनाओं की खोज जारी है।"
        },
        "LOST_TO_FOLLOW_UP": {
            "display": "Follow-Up Inactive",
            "next_step": "Unable to connect. Contact your field worker to resume.",
            "display_hi": "संपर्क टूट गया",
            "next_step_hi": "संपर्क नहीं हो सका। प्रक्रिया जारी रखने के लिए कार्यकर्ता से मिलें।"
        }
    }

    @classmethod
    def is_valid_transition(cls, current_status: str, next_status: str) -> bool:
        cur = (current_status or "").upper()
        nxt = (next_status or "").upper()
        return nxt in cls.ALLOWED_TRANSITIONS.get(cur, set())

    @classmethod
    def is_terminal_status(cls, status: str) -> bool:
        return (status or "").upper() in cls.TERMINAL_STATUSES

    @classmethod
    def get_allowed_next_statuses(cls, current_status: str) -> List[str]:
        cur = (current_status or "").upper()
        return sorted(list(cls.ALLOWED_TRANSITIONS.get(cur, set())))

    @classmethod
    def get_beneficiary_view(cls, status: str, language: str = "en") -> Dict[str, str]:
        info = cls.BENEFICIARY_DISPLAY_MAP.get(
            (status or "").upper(),
            {"display": "In Progress", "next_step": "Your case is being handled by a field worker."}
        )
        if language == "hi":
            return {
                "displayStatus": info.get("display_hi") or info["display"],
                "nextStep": info.get("next_step_hi") or info["next_step"]
            }
        return {
            "displayStatus": info["display"],
            "nextStep": info["next_step"]
        }

    @classmethod
    def to_beneficiary_status(cls, status: str, lang: str = "en") -> Dict[str, str]:
        view = cls.get_beneficiary_view(status, language=lang)
        return {
            "title": view["displayStatus"],
            "description": view["nextStep"]
        }

