# SAP Finance C2C Job Alert Bot

Monitors **Dice**, **Indeed**, and **LinkedIn** every 30 minutes for SAP Finance contract (C2C) roles.
Sends instant alerts to **Telegram** and optionally **WhatsApp** the moment a new posting appears.

---

## What it does

- Searches for: SAP Finance, SAP FICO, SAP FI/CO, SAP S/4HANA Finance, SAP Finance Consultant
- Filters to **C2C / Corp-to-Corp / 1099 contract** roles only
- Flags "no third party" postings for manual review rather than silently dropping them
- Deduplicates across runs using SQLite — you'll never get the same posting twice
- Runs forever, unattended, with automatic restart on failure

---

## Project structure

```
sap_job_alert/
├── main.py                   # Scheduler + pipeline entry point
├── config.py                 # All config via env vars
├── requirements.txt
├── Dockerfile
├── docker-compose.yml        # Local testing
├── render.yaml               # One-click Render.com deploy
├── .env.template             # Copy to .env and fill in secrets
├── scrapers/
│   ├── job_scraper.py        # jobspy wrapper for all 3 sources
│   └── filters.py            # SAP Finance + C2C keyword filters
├── db/
│   └── store.py              # SQLite dedup store
└── notifiers/
    ├── telegram_notifier.py
    └── whatsapp_notifier.py
```

---

## Step 1: Create your Telegram bot (5 minutes)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` — follow prompts, pick a name like `SAP Job Alert`
3. BotFather gives you a **BOT_TOKEN** — copy it
4. Start a chat with your new bot (search its username and press Start)
5. Get your **CHAT_ID**: open `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser after sending any message to the bot. Look for `"chat":{"id":XXXXXXX}` in the response

---

## Step 2: Configure environment

```bash
cp .env.template .env
# Edit .env and fill in at minimum:
#   TELEGRAM_BOT_TOKEN
#   TELEGRAM_CHAT_ID
```

---

## Step 3: Choose deployment (all free options)

### Option A — Render.com (Recommended: easiest, always-on, free)

Render's free **Background Worker** tier runs 24/7, auto-restarts, supports persistent disk.

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Background Worker
3. Connect your GitHub repo
4. Render detects `render.yaml` automatically
5. Go to **Environment** in the Render dashboard
6. Add these environment variables manually:
   - `TELEGRAM_BOT_TOKEN` = your token
   - `TELEGRAM_CHAT_ID` = your chat ID
7. Click **Deploy**

The bot starts immediately and runs forever. Logs are live in the Render dashboard.

**Note:** Render free tier sleeps web services but NOT background workers — this is perfect.

---

### Option B — Railway.app (Alternative free tier)

1. Push repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Go to **Variables** tab → add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
5. Railway auto-builds the Dockerfile and deploys
6. Add a **Volume** at `/data` for DB persistence (free tier: 1GB)

Railway gives $5/month free credit — more than enough for this bot.

---

### Option C — Oracle Cloud Always Free (Best for long-term, zero cost forever)

Oracle's Always Free tier includes 2 AMD VMs (1GB RAM each) — free forever, no credit card billing.

```bash
# 1. Sign up at cloud.oracle.com (free tier, requires credit card for verification only)
# 2. Create an Always Free VM (AMD shape, Ubuntu 22.04)
# 3. SSH into the VM and run:

sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl enable docker && sudo systemctl start docker

git clone https://github.com/YOUR_USERNAME/sap-job-alert.git
cd sap-job-alert

cp .env.template .env
nano .env   # Fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

sudo docker-compose up -d

# Check it's running:
sudo docker-compose logs -f
```

---

### Option D — Local machine (simplest for testing)

```bash
# Prerequisites: Python 3.11+, pip

git clone https://github.com/YOUR_USERNAME/sap-job-alert.git
cd sap-job-alert

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium

cp .env.template .env
# Edit .env with your tokens

mkdir -p /data   # Or change DB_PATH in .env to ./data/jobs.db

python main.py
```

---

## Step 4: Enable WhatsApp (optional)

1. Sign up at [twilio.com](https://twilio.com) (free trial: $15 credit)
2. Go to Messaging → Try it Out → Send a WhatsApp Message
3. Follow sandbox join instructions (send a code to Twilio's WhatsApp number)
4. Add to `.env`:
   ```
   WHATSAPP_ENABLED=true
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token
   WHATSAPP_TO=+12125551234   # your number with country code
   ```

---

## Environment variables reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | From @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | — | Your Telegram chat ID |
| `WHATSAPP_ENABLED` | No | `false` | Enable WhatsApp via Twilio |
| `TWILIO_ACCOUNT_SID` | If WA | — | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | If WA | — | Twilio auth token |
| `WHATSAPP_TO` | If WA | — | Your WhatsApp number (+1xxx) |
| `POLL_INTERVAL_MINUTES` | No | `30` | How often to scrape |
| `HOURS_OLD` | No | `24` | Only fetch jobs posted in last N hours |
| `RESULTS_PER_SOURCE` | No | `50` | Max results per search per source |
| `LOCATION` | No | `United States` | Job search location |
| `DB_PATH` | No | `/data/jobs.db` | SQLite database path |
| `PROXY_URL` | No | — | HTTP proxy for scraper (helps with IP blocks) |

---

## Troubleshooting

**No jobs found:** jobspy may be getting blocked. Try:
- Adding `PROXY_URL` (free proxies: webshare.io free tier)
- Reducing `RESULTS_PER_SOURCE` to 20
- Increasing `HOURS_OLD` to 48

**Telegram message not received:** Verify `TELEGRAM_CHAT_ID` by visiting:
`https://api.telegram.org/bot<TOKEN>/getUpdates` after messaging the bot

**LinkedIn blocking:** LinkedIn is the most aggressive. The bot uses jobspy which rotates headers, but if blocked, set `RESULTS_PER_SOURCE=20` and `POLL_INTERVAL_MINUTES=60`.

**Database not persisting across restarts:** Ensure the volume is mounted at `/data` (Render, Railway, Docker all support this).

---

## Customizing search terms

Edit `SAP_SEARCH_TERMS` in `scrapers/job_scraper.py` to add or remove search queries.
Edit `SAP_TITLE_KEYWORDS` / `SAP_DESCRIPTION_KEYWORDS` in `scrapers/filters.py` for role matching.
Edit `C2C_POSITIVE` / `C2C_EXCLUSIONS` in `scrapers/filters.py` for C2C detection.
