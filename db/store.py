"""
SQLite-backed deduplication store.
Persists seen job URLs so restarts don't re-alert.
"""

import sqlite3
import hashlib
import os
import logging
from datetime import datetime
from config import config

log = logging.getLogger("db")


class JobStore:
    def __init__(self):
        os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT    NOT NULL UNIQUE,
                url      TEXT    NOT NULL,
                title    TEXT,
                company  TEXT,
                site     TEXT,
                seen_at  TEXT    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_hash ON seen_jobs(url_hash);

            CREATE TABLE IF NOT EXISTS alert_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash   TEXT NOT NULL,
                channel    TEXT NOT NULL,
                sent_at    TEXT NOT NULL,
                success    INTEGER NOT NULL DEFAULT 1,
                error_msg  TEXT
            );
        """)
        self.conn.commit()
        log.info(f"DB ready at {config.DB_PATH}")

    @staticmethod
    def _hash(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    def is_seen(self, url: str) -> bool:
        h = self._hash(url)
        row = self.conn.execute(
            "SELECT 1 FROM seen_jobs WHERE url_hash = ?", (h,)
        ).fetchone()
        return row is not None

    def mark_seen(self, job: dict):
        url = job["job_url"]
        h = self._hash(url)
        now = datetime.utcnow().isoformat()
        try:
            self.conn.execute(
                """INSERT OR IGNORE INTO seen_jobs
                   (url_hash, url, title, company, site, seen_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (h, url, job.get("title"), job.get("company"), job.get("site"), now),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already inserted by concurrent call

    def log_alert(self, url: str, channel: str, success: bool, error: str = ""):
        h = self._hash(url)
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO alert_log (url_hash, channel, sent_at, success, error_msg)
               VALUES (?, ?, ?, ?, ?)""",
            (h, channel, now, int(success), error),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
