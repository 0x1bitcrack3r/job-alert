"""
Telegram notifier using python-telegram-bot (sync wrapper).
"""

import logging
import requests
from config import config

log = logging.getLogger("telegram")

SITE_EMOJI = {
    "dice": "🎲",
    "indeed": "🔍",
    "linkedin": "💼",
}


def _truncate(text: str, max_len: int = 300) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


class TelegramNotifier:
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def _build_message(self, job: dict) -> str:
        site_emoji = SITE_EMOJI.get(job.get("site", "").lower(), "📋")
        lines = [
            f"🔔 *New SAP Finance C2C Role* {site_emoji}",
            "",
            f"*{job['title']}*",
            f"🏢 {job['company']}",
            f"📍 {job['location']}",
        ]
        if job.get("rate"):
            lines.append(f"💰 {job['rate']}")
        if job.get("date_posted"):
            lines.append(f"🕒 Posted: {job['date_posted']}")
        if job.get("c2c_note"):
            lines.append(f"\n{job['c2c_note']}")

        # Snippet of description
        if job.get("description"):
            snippet = _truncate(job["description"], 200)
            lines += ["", f"_{snippet}_"]

        lines += ["", f"[🔗 View & Apply]({job['job_url']})"]
        return "\n".join(lines)

    def send(self, job: dict) -> bool:
        message = self._build_message(job)
        success = True
        for chat_id in config.TELEGRAM_CHAT_ID:
            try:
                resp = requests.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                log.info(f"  ✅ Telegram sent to {chat_id}: {job['title']}")
            except Exception as e:
                log.error(f"  ❌ Telegram error for {chat_id}: {e}")
                success = False
        return success

    def _send_plain(self, job: dict) -> bool:
        """Fallback plain-text send (no Markdown parsing)."""
        text = (
            f"New SAP Finance C2C Role\n\n"
            f"{job['title']} @ {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Rate: {job.get('rate', 'N/A')}\n"
            f"Posted: {job.get('date_posted', 'N/A')}\n\n"
            f"{job['job_url']}"
        )
        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            log.error(f"  ❌ Telegram plain fallback error: {e}")
            return False

    def send_startup_message(self):
        """Send a bot-started notification."""
        self.send({
            "title": "SAP Finance C2C Job Alert Bot Started ✅",
            "company": "System",
            "location": config.LOCATION,
            "rate": "",
            "date_posted": "",
            "description": (
                f"Monitoring Dice, Indeed, LinkedIn every "
                f"{config.POLL_INTERVAL_MINUTES} minutes for SAP Finance C2C contract roles."
            ),
            "job_url": "https://t.me",
            "site": "",
            "c2c_note": "",
        })
