import os
import requests
import json
import time

API_KEY = os.environ.get("KEEPA_API_KEY", "")

def fetch_filtered_deals():
    if not API_KEY:
        raise RuntimeError("環境変数 KEEPA_API_KEY が未設定です。")

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
            "priceTypes": 3,
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
                time.sleep(wait_ms / 1000 + 1)
                continue
            except Exception:
                time.sleep(60); continue

        if res.status_code == 500:
            time.sleep(30); continue

        if res.status_code != 200:
            print(f"[!] Page {page} error: {res.status_code} - {res.text}")
            break

        data = res.json()
        deals = data.get("deals", {}).get("dr", [])
        if not deals:
            print(f"[!] Page {page} returned no results. Done.")
            break

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
