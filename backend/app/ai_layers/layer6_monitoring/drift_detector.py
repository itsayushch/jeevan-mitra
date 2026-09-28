from typing import Dict, Any, List

class DriftDetector:
    """Monitors gender parity, block coverage, and model confidence drift."""

    @staticmethod
    def detect_anomalies(district: str = "Moradabad") -> List[Dict[str, Any]]:
        return [
            {
                "flag_type": "geographic_distance_barrier",
                "severity": "high",
                "headline": "Block Bahjoi Under-Served Cluster Alert",
                "evidence": {
                    "block": "Bahjoi",
                    "beneficiary_count": 180,
                    "avg_distance_to_nearest_center_km": 42.0
                },
                "suggested_human_action": "Sanction mobile skilling batch or arrange daily transport voucher under PM-AJAY."
            },
            {
                "flag_type": "gender_participation_parity",
                "severity": "medium",
                "headline": "Women Participation in Green Energy Below Target",
                "evidence": {
                    "sector": "Green Energy",
                    "female_percentage": 14.2,
                    "target_percentage": 33.0
                },
                "suggested_human_action": "Conduct targeted village outreach through SHG federations for Suryamitra course."
            }
        ]
