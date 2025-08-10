# supplement_details.py
# サプリメントASINリスト（JSON）を元にKeepaから詳細データを取得して保存する

import json
import time
import requests

INPUT_FILE = "supplement_asins_deals_filtered.json"
OUTPUT_FILE = "supplement_product_details.json"
KEEPA_API_KEY = "aushlc7f0h78jgeaqo6b904f9ggsickj3854obk1edfus9i82nf2takfqq5qgvpe" 

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    asin_list = json.load(f)

if not asin_list:
    print("⚠️ ASINリストが空です。filter条件を見直してください。")
    exit()

print(f"→ 処理対象ASIN: {len(asin_list)}件")

results = []
BATCH_SIZE = 10

for i in range(0, len(asin_list), BATCH_SIZE):
    batch = asin_list[i:i + BATCH_SIZE]
    print(f"[{i // BATCH_SIZE}] リクエスト: {batch[0]} ～ {batch[-1]}")

    params = {
        "key": KEEPA_API_KEY,
        "domain": 6,
        "asin": ",".join(batch),
        "history": 1
    }

    try:
        response = requests.get("https://api.keepa.com/product", params=params)
        data = response.json()

        if "products" in data:
            count = len(data["products"])
            print(f"    → 成功: {count}件")
            results.extend(data["products"])
        else:
            print("    ⚠️ 'products'キーが存在しません。レスポンス:", data)

        # トークン回復待ち時間（refillInが存在すれば優先）
        refill_ms = data.get("refillIn", 0)
        wait_sec = max(15, refill_ms // 1000 + 2)
        print(f"    ⏳ 次リクエストまで {wait_sec} 秒待機...")
        time.sleep(wait_sec)

    except Exception as e:
        print(f"    ❌ エラー: {e}")
        print("    ⏳ 60秒待機して再試行…")
        time.sleep(60)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ 取得完了: {len(results)}件 → {OUTPUT_FILE} に保存")







with open(INPUT_FILE, "r", encoding="utf-8") as f:
    asin_list = json.load(f)

if not asin_list:
    print("⚠️ ASINリストが空です。filter条件を見直してください。")
    exit()

print(f"→ 処理対象ASIN: {len(asin_list)}件")

results = []
BATCH_SIZE = 10
THROTTLE_TIME = 15  # 秒（API制限対策）

for i in range(0, len(asin_list), BATCH_SIZE):
    batch = asin_list[i:i + BATCH_SIZE]
    print(f"[{i // BATCH_SIZE}] リクエスト: {batch[0]} ～ {batch[-1]}")

    params = {
        "key": KEEPA_API_KEY,
        "domain": 6,
        "asin": ",".join(batch),
        "history": 1
    }

    try:
        response = requests.get("https://api.keepa.com/product", params=params)
        data = response.json()

        if "products" in data:
            count = len(data["products"])
            print(f"    → 成功: {count}件")
            results.extend(data["products"])
        else:
            print("    ⚠️ 'products'キーが存在しません。レスポンス:", data)

    except Exception as e:
        print(f"    ❌ エラー: {e}")

    time.sleep(THROTTLE_TIME)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ 補完完了: {len(results)}件 → {OUTPUT_FILE} に保存")
