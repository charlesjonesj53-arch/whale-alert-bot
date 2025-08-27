import os
import requests
import subprocess
from datetime import datetime
import sys
import time

MAX_ATTEMPTS = 3
TIMESTAMP = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        subprocess.run(["python", "whale_bot.py"], check=True)
        send_telegram(f"✅ Whale Bot v5.4 succeeded on attempt {attempt} at {TIMESTAMP}")
        break
    except subprocess.CalledProcessError:
        send_telegram(f"⚠ Whale Bot v5.4 failed on attempt {attempt} at {TIMESTAMP}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(5)  # short delay before retry
        else:
            sys.exit(1)
