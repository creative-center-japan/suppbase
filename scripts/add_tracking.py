import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
API_URL = "https://api.keepa.com/tracking"

MAIN_DOMAIN_ID = 5  # Amazon.co.jp

with open("ranking_asins.json", "r", encoding="utf-8") as f:
    asins = json.load(f)

payload = {
    "mainDomainId": MAIN_DOMAIN_ID,
    "tracking": [
        {
            "asin": asin,
            "trackingType": "REGULAR"
        }
        for asin in asins[:50]
    ]
}

r = requests.post(
    API_URL,
    params={
        "key": KEEPA_API_KEY,
        "type": "add"
    },
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=60
)

if not r.ok:
    print("status:", r.status_code)
    print("response:", r.text)
    r.raise_for_status()

print(f"[OK] tracking added for {len(payload['tracking'])} ASINs")
