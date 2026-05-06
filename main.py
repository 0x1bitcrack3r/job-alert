"""
SAP Finance C2C Job Alert Bot
Polls Dice, Indeed, LinkedIn every 30 minutes.
Sends new C2C contract postings to Telegram (and optionally WhatsApp).
"""

import logging
import time
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from scrapers.job_scraper import scrape_all
from scrapers.filters import is_sap_finance_role, is_c2c_role
from db.store import JobStore
from notifiers.telegram_notifier import TelegramNotifier
from notifiers.whatsapp_notifier import WhatsAppNotifier
from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log"),
    ],
)
log = logging.getLogger("main")


def run_pipeline():
    log.info("▶ Starting job scrape pipeline...")
    store = JobStore()
    telegram = TelegramNotifier()
    whatsapp = WhatsAppNotifier() if config.WHATSAPP_ENABLED else None

    try:
        jobs = scrape_all()
        log.info(f"  Fetched {len(jobs)} raw jobs from all sources")

        new_count = 0
        filtered_count = 0

        for job in jobs:
            title = job.get("title", "")
            description = job.get("description", "")
            url = job.get("job_url", "")

            if not url:
                continue

            # Filter: SAP Finance role?
            if not is_sap_finance_role(title, description):
                continue

            # Filter: C2C contract?
            c2c_result = is_c2c_role(description)
            if c2c_result == "excluded":
                filtered_count += 1
                continue
            if c2c_result == "manual_review":
                job["c2c_note"] = "⚠️ 'No third party' — verify manually"
            elif c2c_result is False:
                filtered_count += 1
                continue

            # Dedup check
            if store.is_seen(url):
                continue

            store.mark_seen(job)
            new_count += 1

            # Notify
            telegram.send(job)
            if whatsapp:
                whatsapp.send(job)

            # Rate-limit notifications to avoid flood
            time.sleep(1.5)

        log.info(
            f"  ✅ Done — {new_count} new alerts sent, "
            f"{filtered_count} filtered out, "
            f"{len(jobs) - new_count - filtered_count} already seen"
        )

    except Exception as e:
        log.exception(f"Pipeline error: {e}")
        raise


def on_job_error(event):
    log.error(f"Scheduler job failed: {event.exception}")


def main():
    log.info("🚀 SAP Finance C2C Job Alert Bot starting...")

    # Validate config before starting
    config.validate()

    # Run once immediately on start
    run_pipeline()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=config.POLL_INTERVAL_MINUTES,
        id="job_scraper",
        max_instances=1,
        coalesce=True,
    )

    def shutdown(sig, frame):
        log.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log.info(f"⏱ Scheduler running — polling every {config.POLL_INTERVAL_MINUTES} minutes")
    scheduler.start()


if __name__ == "__main__":
    main()
