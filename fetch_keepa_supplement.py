import requests
import json
import time

API_KEY = "aushlc7f0h78jgeaqo6b904f9ggsickj3854obk1edfus9i82nf2takfqq5qgvpe"

def fetch_supplement_deals():
    all_asins = set()
    page = 0

    while True:
        selection = {
            "page": page,
            "domainId": 5,  # 日本のAmazon
            "includeCategories": [
                3457080051,  # サプリメント全般
                169903011,   # ビタミンサプリメント
                169904011,   # ミネラルサプリメント
                169905011,   # ハーブサプリメント
                169909011,   # アミノ酸サプリメント
                169911011,   # ダイエットサプリメント
                3457085051,  # 植物性サプリメント
                3457084051   # 動物性サプリメント
            ],
            "priceTypes": 3,  # Amazon + 出品者
            "sortType": 4,    # ランキング順
            "filterErotic": True,
            "isRangeEnabled": True,
            "isFilterEnabled": True
        }

        res = requests.get("https://api.keepa.com/deal", params={
            "key": API_KEY,
            "selection": json.dumps(selection)
        })

        if res.status_code == 429:
            try:
                data = res.json()
                wait_ms = data.get("refillIn", 60000)
                wait_sec = wait_ms / 1000
                print(f"[!] 429 エラー: {wait_sec:.1f}秒待機します...")
                time.sleep(wait_sec + 1)
                continue
            except Exception:
                print("[!] 429エラー（詳細不明）：60秒待機します")
                time.sleep(60)
                continue

        if res.status_code == 500:
            print("[!] 500エラー：30秒待機して再試行します...")
            time.sleep(30)
            continue

        if res.status_code != 200:
            print(f"[!] Page {page} error: {res.status_code} - {res.text}")
            break

        data = res.json()
        total_results = data.get("totalResults", "N/A")
        if page == 0:
            print(f"[✓] Total Results Found: {total_results}")

        deals = data.get("deals", {}).get("dr", [])
        if not deals:
            print(f"[!] Page {page} returned no results. Done.")
            break

        print(f"[{page}] Retrieved: {len(deals)}")

        for deal in deals:
            asin = deal.get("asin")
            if asin:
                all_asins.add(asin)

        page += 1
        time.sleep(2)

    with open("supplement_asins_deals_filtered.json", "w", encoding="utf-8") as f:
        json.dump(sorted(all_asins), f, ensure_ascii=False, indent=2)

    print(f"[✓] Total ASINs: {len(all_asins)} → saved to supplement_asins_deals_filtered.json")

if __name__ == "__main__":
    fetch_supplement_deals()
