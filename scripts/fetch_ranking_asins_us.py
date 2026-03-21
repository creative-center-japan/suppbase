import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 1  # US
API_URL = "https://api.keepa.com/query"

OUT_FILE = os.environ.get("OUT_FILE", "asins_us_ranking.json")
QUERY_TITLE = os.environ.get("QUERY_TITLE", "protein powder")

QUERY = {
    "page": 0,
    "perPage": 200,
    "title": QUERY_TITLE,
    "hasReviews": True,
}

r = requests.post(
    API_URL,
    params={"key": KEEPA_API_KEY, "domain": DOMAIN_ID},
    json=QUERY,
    timeout=60,
)

if r.status_code == 429:
    try:
        info = r.json()
        refill_in = info.get("refillIn")
        print(f"[429][US] rate limited. refillIn={refill_in}ms -> skip this run")
    except Exception:
        print("[429][US] rate limited -> skip this run")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

    print("[OK][US] ranking ASINs fetched: 0 (rate limited)")
    raise SystemExit(0)

r.raise_for_status()

data = r.json()
asins = data.get("asinList", []) or []

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False, indent=2)

print(f"[OK][US] ranking ASINs fetched: {len(asins)} -> {OUT_FILE}")