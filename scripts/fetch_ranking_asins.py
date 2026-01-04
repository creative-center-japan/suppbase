import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # JP
API_URL = "https://api.keepa.com/query"

OUT_FILE = "asins_protein.json"

# 0件回避のため、まず title キーワードで母集団を作る
QUERY = {
    "page": 0,
    "perPage": 200,
    "title": "プロテイン",
    "hasReviews": True,
    # sort は Finder の仕様に合わせて必要なら調整
    # まずは「検索結果が出る」ことを優先して指定しない
}

r = requests.post(
    API_URL,
    params={"key": KEEPA_API_KEY, "domain": DOMAIN_ID},
    json=QUERY,
    timeout=60,
)
r.raise_for_status()

data = r.json()
asins = data.get("asinList", []) or []

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False, indent=2)

print(f"[OK] ranking ASINs fetched: {len(asins)} -> {OUT_FILE}")
