import os
import json
import re
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

MAIN_DOMAIN_ID = 5  # Amazon.co.jp
MAX_TRACKING = 50   # GitHub Actions + token安全域

ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")

# ---------- ASIN 読み込み ----------
with open("ranking_asins.json", "r", encoding="utf-8") as f:
    raw_asins = json.load(f)

# ---------- 正規ASINだけ通す ----------
valid_asins = []
seen = set()

for asin in raw_asins:
    if not isinstance(asin, str):
        continue
    asin = asin.strip().upper()
    if asin in seen:
        continue
    if ASIN_PATTERN.match(asin):
        valid_asins.append(asin)
        seen.add(asin)

valid_asins = valid_asins[:MAX_TRACKING]

if not valid_asins:
    print("[SKIP] no valid ASINs for tracking")
    exit(0)

print(f"[i] tracking valid ASINs: {len(valid_asins)}")

# ---------- Tracking payload ----------
payload = {
    "mainDomainId": MAIN_DOMAIN_ID,
    "tracking": [
        {
            "asin": asin,
            "trackingType": "REGULAR"
        }
        for asin in valid_asins
    ]
}

# ---------- API 呼び出し ----------
r = requests.post(
    API_URL,
    params={
        "key": KEEPA_API_KEY,
        "type": "add"
    },
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=60
)

if not r.ok:
    print("status:", r.status_code)
    print("response:", r.text)
    r.raise_for_status()

print(f"[OK] tracking added for {len(valid_asins)} ASINs")
