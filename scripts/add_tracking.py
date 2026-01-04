import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

with open("ranking_asins.json", "r") as f:
    asins = json.load(f)

payload = [
    {
        "asin": asin,
        "type": "REGULAR",
        "updateInterval": 12  # 12時間
    }
    for asin in asins[:50]
]

r = requests.post(
    API_URL,
    params={
        "key": KEEPA_API_KEY,
        "type": "add",
    },
    json=payload,
    timeout=60
)

r.raise_for_status()
print("[OK] tracking added")
