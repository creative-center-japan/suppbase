import os
import json
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp
BESTSELLERS_API = "https://api.keepa.com/bestsellers"

CATEGORY_ID = os.environ.get("CATEGORY_ID")
OUT_FILE = os.environ.get("OUT_FILE", "asins.json")

RETRY_COUNT = 3
RETRY_SLEEP = 30  # Best Sellersは重いので長め

if not CATEGORY_ID:
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    print(f"[SKIP] CATEGORY_ID not set -> {OUT_FILE}")
    raise SystemExit(0)

for attempt in range(RETRY_COUNT):
    r = requests.get(
        BESTSELLERS_API,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "category": CATEGORY_ID,
        },
        timeout=60,
    )

    if r.status_code == 429:
        print(f"[429] rate limited (retry {attempt+1}/{RETRY_COUNT})")
        time.sleep(RETRY_SLEEP)
        continue

    r.raise_for_status()
    data = r.json()
    best = data.get("bestSellersList") or data
    asins = best.get("asinList") or []

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(asins, f, ensure_ascii=False, indent=2)

    print(f"[OK] best sellers ASINs fetched: {len(asins)} -> {OUT_FILE}")
    raise SystemExit(0)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump([], f)

print(f"[SKIP] best sellers skipped after retries -> {OUT_FILE}")
