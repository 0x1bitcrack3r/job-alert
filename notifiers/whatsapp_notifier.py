"""
WhatsApp notifier via Twilio WhatsApp API.
Only active when WHATSAPP_ENABLED=true.
"""

import logging
from config import config

log = logging.getLogger("whatsapp")


def _truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


class WhatsAppNotifier:
    def __init__(self):
        try:
            from twilio.rest import Client
            self.client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            self.from_ = config.TWILIO_WHATSAPP_FROM
            self.to = f"whatsapp:{config.WHATSAPP_TO}"
            log.info("WhatsApp notifier ready")
        except ImportError:
            log.warning("twilio package not installed — WhatsApp disabled")
            self.client = None

    def _build_message(self, job: dict) -> str:
        parts = [
            "🔔 New SAP Finance C2C Role",
            "",
            f"*{job['title']}*",
            f"Company: {job['company']}",
            f"Location: {job['location']}",
        ]
        if job.get("rate"):
            parts.append(f"Rate: {job['rate']}")
        if job.get("date_posted"):
            parts.append(f"Posted: {job['date_posted']}")
        if job.get("c2c_note"):
            parts.append(job["c2c_note"])
        parts += ["", job["job_url"]]
        return "\n".join(parts)

    def send(self, job: dict) -> bool:
        if not self.client:
            return False
        try:
            body = self._build_message(job)
            msg = self.client.messages.create(
                from_=self.from_,
                to=self.to,
                body=body,
            )
            log.info(f"  ✅ WhatsApp sent: {msg.sid}")
            return True
        except Exception as e:
            log.error(f"  ❌ WhatsApp error: {e}")
            return False
