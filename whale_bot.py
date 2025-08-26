#!/usr/bin/env python3
import os
import requests
import re
import subprocess
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
MIN_USD = int(os.environ.get('MIN_USD', '10000000'))  # default 10,000,000

LAST_FILE = 'last_seen.txt'
URL = 'https://whale-alert.io/alerts.html'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; WhaleScraper/1.0)'}

def read_last():
    if os.path.exists(LAST_FILE):
        return open(LAST_FILE, 'r', encoding='utf-8').read().strip()
    return ''

def write_last(text):
    with open(LAST_FILE, 'w', encoding='utf-8') as f:
        f.write(text)

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    r = requests.post(url, data=payload, timeout=15)
    print("telegram status", r.status_code, r.text)
    return r.ok

def parse_alerts(html):
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []
    # find elements likely to contain alerts
    for el in soup.find_all(['div','li','tr','p','span']):
        txt = el.get_text(separator=' ', strip=True)
        if not txt:
            continue
        # heuristic: must mention BTC and a dollar amount
        if 'BTC' in txt and '$' in txt:
            candidates.append(txt)
    # dedupe, keep order
    seen = set(); out = []
    for t in candidates:
        if t in seen: continue
        seen.add(t); out.append(t)
    return out

def extract_usd(text):
    m = re.search(r'\$([\d,]+)', text)
    if not m:
        return 0
    return int(m.group(1).replace(',', ''))

def git_commit_and_push():
    try:
        subprocess.run(['git', 'config', 'user.name', 'github-actions[bot]'], check=True)
        subprocess.run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'], check=True)
        subprocess.run(['git', 'add', LAST_FILE], check=True)
        res = subprocess.run(['git', 'commit', '-m', 'update last_seen'], check=False, capture_output=True, text=True)
        print(res.stdout, res.stderr)
        subprocess.run(['git', 'push', 'origin', 'HEAD:main'], check=True)
    except Exception as e:
        print("git push failed", e)

def main():
    last = read_last()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print("Fetch error:", e)
        return

    alerts = parse_alerts(r.text)
    if not alerts:
        print("No alerts parsed")
        return

    # alerts likely newest first; we want oldest->newest so messages send in order
    alerts = list(reversed(alerts))
    new_last = last
    sent = False

    for alert in alerts:
        usd = extract_usd(alert)
        if usd >= MIN_USD and alert != last:
            msg = f"🐋 Whale Alert:\n{alert}"
            ok = send_telegram(msg)
            if ok:
                new_last = alert
                sent = True

    if sent:
        write_last(new_last)
        git_commit_and_push()
    else:
        print("No new alerts meeting threshold")

if __name__ == '__main__':
    main()
