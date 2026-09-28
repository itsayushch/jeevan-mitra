from typing import Dict, Any

class SummaryEngine:
    """Generates concise case summaries for field workers to review uncertain transcripts."""

    @staticmethod
    def generate_case_summary(beneficiary: Dict[str, Any], profile_answers: list) -> str:
        name = beneficiary.get("name", "Beneficiary")
        village = beneficiary.get("village", "Unknown")
        category = beneficiary.get("category", "SC")

        lines = [f"Case Summary for {name} ({category}, Village: {village}):"]
        for ans in profile_answers:
            field = ans.get("field_name")
            val = ans.get("field_value")
            conf = ans.get("confidence_score", 1.0)
            status = "Verified" if conf > 0.85 else "Needs Verification"
            lines.append(f"- {field}: {val} [{status}]")

        return "\n".join(lines)
