import os
import json
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 1  # US
BESTSELLERS_API = "https://api.keepa.com/bestsellers"

CATEGORY_ID = os.environ.get("CATEGORY_ID")
OUT_FILE = os.environ.get("OUT_FILE", "asins_us_bestsellers.json")

RETRY = 3
SLEEP = 60

if not CATEGORY_ID:
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print("[SKIP][US] CATEGORY_ID not set")
    raise SystemExit(0)

for i in range(RETRY):
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
        print(f"[429][US] rate limited (retry {i+1}/{RETRY})")
        time.sleep(SLEEP)
        continue

    r.raise_for_status()
    data = r.json()
    best = data.get("bestSellersList") or data
    asins = best.get("asinList") or []

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(asins, f, ensure_ascii=False, indent=2)

    print(f"[OK][US] fetched {len(asins)} bestseller ASINs -> {OUT_FILE}")
    raise SystemExit(0)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump([], f, ensure_ascii=False, indent=2)

print("[SKIP][US] best sellers skipped after retries")