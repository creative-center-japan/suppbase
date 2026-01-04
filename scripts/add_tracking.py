import os
import json
import re
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

MAIN_DOMAIN_ID = 5
MAX_TRACKING = 50
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")

IN_FILE = "asins_protein.json"

with open(IN_FILE, "r", encoding="utf-8") as f:
    raw_asins = json.load(f)

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
    raise SystemExit(0)

payload = {
    "mainDomainId": MAIN_DOMAIN_ID,
    "tracking": [{"asin": a, "trackingType": "REGULAR"} for a in valid_asins],
}

r = requests.post(
    API_URL,
    params={"key": KEEPA_API_KEY, "type": "add"},
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=60,
)

if not r.ok:
    print("status:", r.status_code)
    print("response:", r.text)
    r.raise_for_status()

print(f"[OK] tracking added for {len(valid_asins)} ASINs")
