import os
import json
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5

ASIN_FILE = "asins_supplement.json"
OUT_FILE = "supplement_product_details.json"

def safe_int(v):
    return v if isinstance(v, int) and v > 0 else None

def fetch(asins):
    rows = []

    for i in range(0, len(asins), 50):
        batch = asins[i:i+50]

        while True:
            r = requests.get(
                "https://api.keepa.com/product",
                params={
                    "key": API_KEY,
                    "domain": DOMAIN_ID,
                    "asin": ",".join(batch),
                    "stats": 1,
                    "buybox": 1,
                    "history": 0,
                },
                timeout=60,
            )

            if r.status_code == 429:
                refill_ms = r.json().get("refillIn", 60000)
                wait_sec = int(refill_ms / 1000) + 5
                print(f"[429] sleep {wait_sec}s")
                time.sleep(wait_sec)
                continue

            r.raise_for_status()
            break

        data = r.json()

        for p in data.get("products", []):
            stats = p.get("stats") or {}

            rows.append({
                "asin": p.get("asin"),

                # price
                "price": safe_int(stats.get("buyBoxPrice")) or safe_int(stats.get("avg90")),

                # ranking / review / rating（★修正点）
                "salesrank": safe_int(stats.get("salesRank")),
                "reviewcount": safe_int(stats.get("reviewCount")),
                "rating": stats.get("rating"),

                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        time.sleep(30)

    return rows

with open(ASIN_FILE, "r", encoding="utf-8") as f:
    asins = json.load(f)

rows = fetch(asins)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print(f"[OK] supplement fetched {len(rows)} rows")
