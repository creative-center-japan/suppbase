import os
import json
import re
import requests
import time

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

MAIN_DOMAIN_ID = 5
MAX_TRACKING = 50
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")

IN_FILE = "asins_protein.json"

with open(IN_FILE, "r", encoding="utf-8") as f:
    raw_asins = json.load(f)

# 正規ASINのみ
asins = []
seen = set()
for a in raw_asins:
    if isinstance(a, str):
        a = a.strip().upper()
        if ASIN_PATTERN.match(a) and a not in seen:
            asins.append(a)
            seen.add(a)

asins = asins[:MAX_TRACKING]

if not asins:
    print("[SKIP] no valid ASINs")
    raise SystemExit(0)

success = 0
failed = 0

for asin in asins:
    payload = {
        "mainDomainId": MAIN_DOMAIN_ID,
        "tracking": [
            {
                "asin": asin,
                "trackingType": "REGULAR"
            }
        ]
    }

    r = requests.post(
        API_URL,
        params={"key": KEEPA_API_KEY, "type": "add"},
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if r.ok:
        success += 1
        print(f"[OK] tracking added: {asin}")
    else:
        failed += 1
        print(f"[SKIP] tracking failed: {asin}")
        # invalid ASIN は無視して続行
        time.sleep(1)
        continue

    time.sleep(1)  # Keepa対策

print(f"[DONE] tracking success={success}, failed={failed}")
