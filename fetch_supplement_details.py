# fetch_supplement_details.py

import json
import time
import requests

INPUT_FILE = "supplement_asins_deals_filtered.json"
OUTPUT_FILE = "supplement_product_details.json"
KEEPA_API_KEY = "aushlc7f0h78jgeaqo6b904f9ggsickj3854obk1edfus9i82nf2takfqq5qgvpe" 

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    asin_data = json.load(f)

asins = asin_data if isinstance(asin_data, list) else asin_data.get("asins", [])

print(f"Total ASINs: {len(asins)}")

results = []
BATCH_SIZE = 20
THROTTLE_TIME = 2

for i in range(0, len(asins), BATCH_SIZE):
    batch = asins[i:i + BATCH_SIZE]
    print(f"[{i//BATCH_SIZE}] Fetching batch: {batch[0]} - {batch[-1]}")

    params = {
        "key": KEEPA_API_KEY,
        "domain": "co.jp",
        "asin": ",".join(batch),
        "history": 1
    }

    try:
        res = requests.get("https://api.keepa.com/product", params=params)
        data = res.json()
        results.extend(data.get("products", []))
        print(f"→ Retrieved {len(data.get('products', []))} items")
    except Exception as e:
        print(f"Error fetching batch: {e}")

    time.sleep(THROTTLE_TIME)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ Supplement details saved to {OUTPUT_FILE}")
