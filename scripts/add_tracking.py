import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

# ranking_asins.json を前段で生成している前提
with open("ranking_asins.json", "r", encoding="utf-8") as f:
    asins = json.load(f)

# 上位50件だけ tracking
payload = [
    {
        "asin": asin,
        "trackingType": "REGULAR"
    }
    for asin in asins[:50]
]

r = requests.post(
    API_URL,
    params={
        "key": KEEPA_API_KEY,
        "type": "add"
    },
    json=payload,
    timeout=60
)

# ★ 400 のときは内容を見る
if not r.ok:
    print("status:", r.status_code)
    print("response:", r.text)
    r.raise_for_status()

print(f"[OK] tracking added for {len(payload)} ASINs")
