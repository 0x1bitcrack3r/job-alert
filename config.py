"""
Configuration — all secrets come from environment variables.
Never hard-code credentials here.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    TELEGRAM_CHAT_ID: list[str] = field(
    default_factory=lambda: [
        cid.strip()
        for cid in os.getenv("TELEGRAM_CHAT_ID", "").split(",")
        if cid.strip()
    ]
)

    # WhatsApp (Twilio) — optional
    WHATSAPP_ENABLED: bool = field(default_factory=lambda: os.getenv("WHATSAPP_ENABLED", "false").lower() == "true")
    TWILIO_ACCOUNT_SID: str = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""))
    TWILIO_AUTH_TOKEN: str = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", ""))
    TWILIO_WHATSAPP_FROM: str = field(default_factory=lambda: os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"))
    WHATSAPP_TO: str = field(default_factory=lambda: os.getenv("WHATSAPP_TO", ""))

    # Scraper
    POLL_INTERVAL_MINUTES: int = field(default_factory=lambda: int(os.getenv("POLL_INTERVAL_MINUTES", "30")))
    HOURS_OLD: int = field(default_factory=lambda: int(os.getenv("HOURS_OLD", "24")))
    RESULTS_PER_SOURCE: int = field(default_factory=lambda: int(os.getenv("RESULTS_PER_SOURCE", "50")))
    LOCATION: str = field(default_factory=lambda: os.getenv("LOCATION", "United States"))

    # Database
    DB_PATH: str = field(default_factory=lambda: os.getenv("DB_PATH", "/data/jobs.db"))

    # Proxy (optional, helps avoid IP blocks)
    PROXY_URL: str = field(default_factory=lambda: os.getenv("PROXY_URL", ""))

    def validate(self):
        errors = []
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        if not self.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required")
        if self.WHATSAPP_ENABLED:
            if not self.TWILIO_ACCOUNT_SID:
                errors.append("TWILIO_ACCOUNT_SID required when WHATSAPP_ENABLED=true")
            if not self.TWILIO_AUTH_TOKEN:
                errors.append("TWILIO_AUTH_TOKEN required when WHATSAPP_ENABLED=true")
            if not self.WHATSAPP_TO:
                errors.append("WHATSAPP_TO required when WHATSAPP_ENABLED=true")
        if errors:
            raise EnvironmentError("Config errors:\n" + "\n".join(f"  - {e}" for e in errors))


config = Config()
