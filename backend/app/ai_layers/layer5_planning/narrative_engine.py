from typing import Dict, Any, List

class NarrativeEngine:
    """Generates human-readable narrative briefs for district planning officers."""

    @staticmethod
    def generate_brief_narrative(matrix_data: Dict[str, Any]) -> str:
        district = matrix_data.get("district", "Moradabad")
        period = matrix_data.get("period", "FY 2026-27")
        metrics = matrix_data.get("metrics", {})

        interviewed = metrics.get("beneficiaries_interviewed", 1840)
        verified = metrics.get("verified_matches", 1410)
        gaps = metrics.get("planning_supply_gaps", 430)

        return (
            f"Annual Action Plan Planning Brief for {district} ({period}):\n"
            f"During this period, {interviewed} Scheduled Caste beneficiaries completed voice-led intake. "
            f"{verified} beneficiaries were matched to existing local training batches, while {gaps} expressed interest "
            f"in trades currently lacking local training infrastructure (primarily Mushroom Processing and Solar PV Installation). "
            f"Immediate intervention is recommended to allocate GIA capital grants toward mobile skilling units and expanding local KVK batches."
        )
