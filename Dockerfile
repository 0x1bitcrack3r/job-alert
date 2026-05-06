FROM python:3.12-slim

# Install Playwright system deps
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgbm1 libasound2 libxrandr2 libxdamage1 libxcomposite1 \
    libxfixes3 libxext6 libx11-6 libpango-1.0-0 libcairo2 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (chromium only — smallest footprint)
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Data dir for SQLite DB
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/data/jobs.db

CMD ["python", "main.py"]
