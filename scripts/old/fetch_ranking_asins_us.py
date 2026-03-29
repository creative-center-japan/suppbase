import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]

# Keepa domain: 1=JP, 2=US
DOMAIN_ID = int(os.environ.get("DOMAIN_ID", "2"))
API_URL = "https://api.keepa.com/query"

OUT_FILE = os.environ.get("OUT_FILE", "asins_us_ranking.json")
QUERY_TITLE = os.environ.get("QUERY_TITLE", "protein powder")
PER_PAGE = int(os.environ.get("PER_PAGE", "200"))

QUERY = {
    "page": 0,
    "perPage": PER_PAGE,
    "title": QUERY_TITLE,
    "hasReviews": True,
}


def write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


try:
    r = requests.post(
        API_URL,
        params={"key": KEEPA_API_KEY, "domain": DOMAIN_ID},
        json=QUERY,
        timeout=60,
    )
except requests.RequestException as e:
    print(f"[ERROR][US] query request failed: {e}")
    write_json(OUT_FILE, [])
    raise SystemExit(1)

if r.status_code == 429:
    try:
        info = r.json()
        refill_in = info.get("refillIn")
        print(f"[429][US] rate limited. refillIn={refill_in}ms -> skip this run")
    except Exception:
        print("[429][US] rate limited -> skip this run")

    write_json(OUT_FILE, [])
    print("[OK][US] ranking ASINs fetched: 0 (rate limited)")
    raise SystemExit(0)

r.raise_for_status()

data = r.json()
asins = data.get("asinList", []) or []

write_json(OUT_FILE, asins)
print(f"[OK][US] ranking ASINs fetched: {len(asins)} -> {OUT_FILE}")