from typing import Dict, Any, List

class AdvisoryQueue:
    """Manages active advisories flagged for District Welfare Officers."""

    @staticmethod
    def list_open_advisories(district: str = "Moradabad") -> List[Dict[str, Any]]:
        return [
            {
                "id": "adv_01",
                "district": district,
                "flag_type": "spatial_supply_gap",
                "severity": "high",
                "headline": "Bahjoi Mushroom & Agro Demand Exceeds Supply by 180 seats",
                "status": "open"
            },
            {
                "id": "adv_02",
                "district": district,
                "flag_type": "waitlist_congestion",
                "severity": "medium",
                "headline": "Civil Lines Retail Hub Waitlist at 180 beneficiaries",
                "status": "acknowledged"
            }
        ]
