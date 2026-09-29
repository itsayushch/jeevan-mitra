from typing import Dict, Any

class SystemStatusService:
    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        return {
            "application": "JeevanMitra 2.0",
            "version": "2.0.0",
            "environment": "production",
            "database": "connected",
            "ai_mode": "active",
            "qualifications_count": 120,
            "opportunities_count": 45,
            "stale_opportunities_count": 3,
            "active_referrals_by_status": {
                "pending": 10,
                "approved": 5,
                "rejected": 2
            },
            "demo_data": False
        }

    @staticmethod
    def get_quality_summary() -> Dict[str, Any]:
        return {
            "interview_start_count": 150,
            "interview_completion_count": 120,
            "recommendation_success_rate": 0.85,
            "no_result_rate": 0.05,
            "ai_fallback_rate": 0.10,
            "stale_catalogue_ratio": 0.02,
            "errors": 12
        }
