import os
import json
import requests
import time

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # JP
API_URL = "https://api.keepa.com/query"

OUT_FILE = "asins_protein.json"

QUERY = {
    "page": 0,
    "perPage": 200,
    "title": "プロテイン",
    "hasReviews": True,
}

r = requests.post(
    API_URL,
    params={"key": KEEPA_API_KEY, "domain": DOMAIN_ID},
    json=QUERY,
    timeout=60,
)

# ===== 429 は正常系 =====
if r.status_code == 429:
    try:
        info = r.json()
        refill_in = info.get("refillIn")
        print(f"[429] rate limited. refillIn={refill_in}ms → skip this run")
    except Exception:
        print("[429] rate limited → skip this run")

    # 空ファイルを出して後続を止める
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

    print("[OK] ranking ASINs fetched: 0 (rate limited)")
    raise SystemExit(0)

# ===== それ以外の異常だけ落とす =====
r.raise_for_status()

data = r.json()
asins = data.get("asinList", []) or []

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False, indent=2)

print(f"[OK] ranking ASINs fetched: {len(asins)}")
