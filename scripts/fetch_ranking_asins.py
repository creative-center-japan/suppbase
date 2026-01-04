import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # JP

API_URL = "https://api.keepa.com/query"

OUT_FILE = "ranking_asins.json"

query = {
    "page": 0,
    "perPage": 100,
    "rootCategory": [3167641],  # プロテイン系カテゴリ（例）
    "current_NEW_gte": 1000,
    "current_NEW_lte": 10000,
    "hasReviews": True,
    "sort": [
        ["current_SALES", "asc"]
    ]
}

r = requests.post(
    API_URL,
    params={
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
    },
    json=query,
    timeout=60
)

r.raise_for_status()
data = r.json()

asins = data.get("asinList", [])

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False, indent=2)

print(f"[OK] ranking ASINs fetched: {len(asins)}")
