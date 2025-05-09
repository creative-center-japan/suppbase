import requests
import json
import time
from pathlib import Path

# ASINファイルの読み込み
# ASIN_FILE = Path("/mnt/data/protein_asins_deals_filtered.json")
# OUTPUT_FILE = Path("/mnt/data/product_details.json")


# 修正後（ローカル用）
ASIN_FILE = Path("protein_asins_deals_filtered.json")
OUTPUT_FILE = Path("product_details.json")


API_KEY = "aushlc7f0h78jgeaqo6b904f9ggsickj3854obk1edfus9i82nf2takfqq5qgvpe"
DOMAIN_ID = 5  # 日本

# ASINリスト読み込み
with open(ASIN_FILE, "r", encoding="utf-8") as f:
    asin_list = json.load(f)

# 100件ずつ分割
BATCH_SIZE = 100
product_results = []
for i in range(0, len(asin_list), BATCH_SIZE):
    batch = asin_list[i:i + BATCH_SIZE]
    asins = ",".join(batch)

    url = f"https://api.keepa.com/product?key={API_KEY}&domain={DOMAIN_ID}&asin={asins}&stats=180"
    res = requests.get(url)

    if res.status_code == 429:
        print(f"[!] 429 Too Many Requests - waiting 60s")
        time.sleep(60)
        continue

    if res.status_code != 200:
        print(f"[!] Error: {res.status_code}")
        break

    data = res.json()
    product_results.extend(data.get("products", []))
    print(f"[{i//BATCH_SIZE}] Retrieved {len(data.get('products', []))} products")
    time.sleep(1.2)  # トークン節約

# 結果保存
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(product_results, f, ensure_ascii=False, indent=2)

OUTPUT_FILE.name
