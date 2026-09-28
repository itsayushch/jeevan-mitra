from typing import Dict, Any

class OutboundMessaging:
    """Templates and dispatches notification SMS and WhatsApp messages for verified referrals."""

    @staticmethod
    def generate_sms(beneficiary_name: str, course_title: str, centre_name: str, batch_date: str) -> str:
        return (
            f"Namaste {beneficiary_name}, your skilling batch for {course_title} at {centre_name} "
            f"starts on {batch_date}. Please contact your field-worker for stipend and kit details (PM-AJAY GIA)."
        )

    @staticmethod
    def generate_whatsapp(beneficiary_name: str, course_title: str, centre_name: str, batch_date: str) -> str:
        return (
            f"🌟 *PM-AJAY Livelihood Opportunity Confirmed*\n\n"
            f"Hello {beneficiary_name},\n"
            f"Your training enrolment in *{course_title}* at *{centre_name}* is verified!\n"
            f"📅 *Batch Start Date:* {batch_date}\n"
            f"💰 *Stipend:* ₹1,500/month DBT\n\n"
            f"A representative will contact you shortly."
        )
