import requests
import json
import time

API_KEY = "aushlc7f0h78jgeaqo6b904f9ggsickj3854obk1edfus9i82nf2takfqq5qgvpe"

def fetch_filtered_deals():
    all_asins = set()
    page = 0

    while True:
        selection = {
            "page": page,
            "domainId": 5,
            "includeCategories": [
                3457069051, 3457070051, 3457071051, 3457072051, 3457073051,
                3457074051, 3457076051, 3457077051, 3457079051, 10504322051,
                10504306051, 24310670051, 10504317051, 24555189051, 10504304051,
                6637456051, 16402319051, 10504302051, 10504294051
            ],
            "priceTypes": 3,  # Amazon + 出品者
            "sortType": 4,
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
                continue  # 同じページでリトライ
            except Exception:
                print("[!] 429 だけど詳細不明なので60秒待機します")
                time.sleep(60)
                continue

        if res.status_code == 500:
            print("[!] 500エラー：サーバ側の問題。30秒待機して再試行します...")
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

    with open("protein_asins_deals_filtered.json", "w", encoding="utf-8") as f:
        json.dump(sorted(all_asins), f, ensure_ascii=False, indent=2)

    print(f"[✓] Total ASINs: {len(all_asins)} → saved to protein_asins_deals_filtered.json")

if __name__ == "__main__":
    fetch_filtered_deals()
