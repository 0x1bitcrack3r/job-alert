"""
Scrapes Dice, Indeed, and LinkedIn using jobspy.
Falls back gracefully if one source fails.
"""

import logging
import time
import random
import pandas as pd
from typing import Optional
from config import config
import itertools


log = logging.getLogger("scraper")

SAP_SEARCH_TERMS = [

    # --- Core FICO variants ---
    "SAP Finance Consultant C2C",
    "SAP FICO Consultant C2C",
    "SAP S4HANA Finance C2C",
    "SAP FI CO contract",
    "SAP FICO Consultant C2C contract",
    "SAP FI CO Consultant corp to corp",
    "SAP FICO Functional Consultant C2C",
    "SAP FICO Senior Consultant contract",
    "SAP FICO Lead C2C",
    "SAP FI Consultant C2C",
    "SAP CO Consultant C2C",
    "SAP FI CO Lead corp to corp",

    # --- S/4HANA Finance variants ---
    "SAP S4HANA Finance Consultant C2C",
    "SAP S/4HANA Finance C2C contract",
    "SAP S4HANA FICO C2C",
    "SAP S/4HANA FICO Consultant corp to corp",
    "SAP S4 Finance Functional C2C",
    "SAP S/4HANA Financial Accounting contract",
    "SAP S4HANA Central Finance C2C",

    # --- Financial Accounting (FI) module specifics ---
    "SAP Financial Accounting Consultant C2C",
    "SAP General Ledger Consultant C2C",
    "SAP GL Consultant contract",
    "SAP Accounts Payable Consultant C2C",
    "SAP AP Consultant corp to corp",
    "SAP Accounts Receivable Consultant C2C",
    "SAP AR Consultant contract",
    "SAP Asset Accounting Consultant C2C",
    "SAP AA Consultant corp to corp",
    "SAP Bank Accounting Consultant C2C",
    "SAP New GL Consultant C2C",

    # --- Controlling (CO) module specifics ---
    "SAP Controlling Consultant C2C",
    "SAP CO CCA Consultant contract",
    "SAP Cost Center Accounting C2C",
    "SAP Profit Center Accounting Consultant C2C",
    "SAP Product Costing Consultant C2C",
    "SAP COPA Consultant C2C",
    "SAP Profitability Analysis Consultant contract",
    "SAP CO PA Consultant corp to corp",
    "SAP Internal Orders Consultant C2C",

    # --- Job title level variants ---
    "SAP Finance Functional Analyst C2C",
    "SAP FICO Business Analyst C2C",
    "SAP Finance Solution Architect C2C",
    "SAP FICO Architect corp to corp",
    "SAP Finance Project Manager C2C",
    "SAP Finance Manager contract",
    "SAP Finance Director C2C",
    "SAP FICO SME C2C",
    "SAP Finance Subject Matter Expert contract",
    "SAP FICO Team Lead C2C",
    "SAP Finance Program Manager C2C",

    # --- Implementation / rollout context ---
    "SAP FICO Implementation Consultant C2C",
    "SAP Finance Implementation contract",
    "SAP FICO Rollout Consultant C2C",
    "SAP Finance Migration Consultant C2C",
    "SAP FICO Upgrade Consultant contract",
    "SAP Finance Transformation C2C",
    "SAP FICO Configuration Consultant C2C",
    "SAP Finance Support Consultant C2C",
    "SAP FICO AMS Consultant C2C",

    # --- Treasury & related Finance modules ---
    "SAP Treasury Consultant C2C",
    "SAP TRM Consultant contract",
    "SAP Cash Management Consultant C2C",
    "SAP BCM Consultant C2C",
    "SAP FSCM Consultant C2C",
    "SAP Financial Supply Chain C2C",
    "SAP Credit Management Consultant C2C",
    "SAP Dispute Management Consultant C2C",
    "SAP Collection Management Consultant C2C",

    # --- Industry / domain qualifiers ---
    "SAP FICO Healthcare Consultant C2C",
    "SAP Finance Manufacturing Consultant C2C",
    "SAP FICO Utilities Consultant C2C",
    "SAP Finance Retail Consultant C2C",
    "SAP FICO Public Sector Consultant C2C",
    "SAP Finance Banking Consultant C2C",
    "SAP FICO Insurance Consultant C2C",
    "SAP Finance Oil Gas Consultant C2C",

    # --- Without explicit C2C — catches postings that mention it only in body ---
    "SAP FICO Consultant contract remote",
    "SAP Finance Consultant contract remote",
    "SAP S4HANA Finance contract remote",
    "SAP FICO contract 1099",
    "SAP Finance 1099 contract",
    "SAP FI CO independent contractor",
    "SAP FICO freelance contract",

]

SOURCES = ["dice", "indeed", "linkedin"]

# In job_scraper.py — replace SAP_SEARCH_TERMS list with this rotation logic
_term_cycle = itertools.cycle([
    SAP_SEARCH_TERMS[i:i+8] for i in range(0, len(SAP_SEARCH_TERMS), 8)
])

def get_current_terms() -> list[str]:
    """Returns the next batch of 8 search terms on each call."""
    return next(_term_cycle)


def scrape_source(site: str, search_term: str) -> list[dict]:
    """Scrape a single source with retry logic."""
    from jobspy import scrape_jobs

    for attempt in range(3):
        try:
            proxy = {"http": config.PROXY_URL, "https": config.PROXY_URL} if config.PROXY_URL else None

            kwargs = dict(
                site_name=[site],
                search_term=search_term,
                location=config.LOCATION,
                job_type="contract",
                results_wanted=config.RESULTS_PER_SOURCE,
                hours_old=config.HOURS_OLD,
                country_indeed="USA",
                linkedin_fetch_description=True,  # needed for C2C keyword detection
                verbose=0,
            )
            if proxy:
                kwargs["proxies"] = proxy

            df: pd.DataFrame = scrape_jobs(**kwargs)
            if df is None or df.empty:
                return []

            jobs = df.to_dict("records")
            log.info(f"  [{site}] '{search_term}' → {len(jobs)} results")
            return jobs

        except Exception as e:
            wait = (attempt + 1) * 5 + random.uniform(0, 3)
            log.warning(f"  [{site}] attempt {attempt+1} failed: {e}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

    log.error(f"  [{site}] all retries exhausted for '{search_term}'")
    return []


def normalize_job(raw: dict) -> Optional[dict]:
    """Normalize raw jobspy record into a consistent shape."""
    url = str(raw.get("job_url") or raw.get("url") or "").strip()
    if not url or url == "nan":
        return None

    title = str(raw.get("title") or "").strip()
    company = str(raw.get("company") or "").strip()
    location = str(raw.get("location") or "Remote").strip()
    description = str(raw.get("description") or "").strip()
    date_posted = str(raw.get("date_posted") or raw.get("posted_at") or "").strip()
    site = str(raw.get("site") or "").strip()
    min_amount = raw.get("min_amount")
    max_amount = raw.get("max_amount")
    currency = raw.get("currency", "USD")
    interval = raw.get("interval", "")

    # Build rate string
    rate = ""
    if min_amount and str(min_amount) not in ("nan", "None"):
        rate = f"${float(min_amount):,.0f}"
        if max_amount and str(max_amount) not in ("nan", "None"):
            rate += f" – ${float(max_amount):,.0f}"
        if interval:
            rate += f"/{interval}"

    return {
        "title": title,
        "company": company,
        "location": location,
        "description": description,
        "job_url": url,
        "date_posted": date_posted,
        "site": site,
        "rate": rate,
        "currency": currency,
        "c2c_note": "",
    }


def scrape_all() -> list[dict]:
    """
    Scrape all sources for all search terms.
    Returns deduplicated list of normalized job dicts.
    """
    seen_urls: set[str] = set()
    all_jobs: list[dict] = []

    for term in get_current_terms():
        for site in SOURCES:
            raw_jobs = scrape_source(site, term)
            for raw in raw_jobs:
                job = normalize_job(raw)
                if job and job["job_url"] not in seen_urls:
                    seen_urls.add(job["job_url"])
                    all_jobs.append(job)
            # Be polite between requests
            time.sleep(random.uniform(2, 5))

    log.info(f"Total unique jobs before filtering: {len(all_jobs)}")
    return all_jobs
