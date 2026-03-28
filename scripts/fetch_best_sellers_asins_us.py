import os
import json
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]

# Keepa domain: 1=JP, 2=US
DOMAIN_ID = int(os.environ.get("DOMAIN_ID", "2"))
BESTSELLERS_API = "https://api.keepa.com/bestsellers"

CATEGORY_ID = os.environ.get("CATEGORY_ID")
OUT_FILE = os.environ.get("OUT_FILE", "asins_us_bestsellers.json")

RETRY = int(os.environ.get("RETRY", "3"))
SLEEP = int(os.environ.get("SLEEP", "60"))


def write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if not CATEGORY_ID:
    write_json(OUT_FILE, [])
    print("[SKIP][US] CATEGORY_ID not set")
    raise SystemExit(0)

for i in range(RETRY):
    try:
        r = requests.get(
            BESTSELLERS_API,
            params={
                "key": KEEPA_API_KEY,
                "domain": DOMAIN_ID,
                "category": CATEGORY_ID,
            },
            timeout=60,
        )
    except requests.RequestException as e:
        print(f"[ERROR][US] request failed (retry {i+1}/{RETRY}): {e}")
        if i < RETRY - 1:
            time.sleep(SLEEP)
            continue
        write_json(OUT_FILE, [])
        raise SystemExit(1)

    if r.status_code == 429:
        print(f"[429][US] rate limited (retry {i+1}/{RETRY})")
        if i < RETRY - 1:
            time.sleep(SLEEP)
            continue
        write_json(OUT_FILE, [])
        print("[SKIP][US] best sellers skipped after retries")
        raise SystemExit(0)

    r.raise_for_status()
    data = r.json()

    best = data.get("bestSellersList") or data
    if isinstance(best, dict):
        asins = best.get("asinList") or []
    elif isinstance(best, list):
        asins = best
    else:
        asins = []

    write_json(OUT_FILE, asins)
    print(f"[OK][US] fetched {len(asins)} bestseller ASINs -> {OUT_FILE}")
    raise SystemExit(0)

write_json(OUT_FILE, [])
print("[SKIP][US] best sellers skipped after retries")