# scripts/fetch_filtered_deals.py  （差し替え）
import os
import requests
import json
import time
from pathlib import Path

API_KEY = os.environ.get("KEEPA_API_KEY", "")

OUT_ASINS = Path("protein_asins_deals_filtered.json")
OUT_DROPS = Path("data/deal_price_drops_protein.json")  # ★ 追加: ASIN→priceDrops

def fetch_filtered_deals():
    if not API_KEY:
        raise RuntimeError("環境変数 KEEPA_API_KEY が未設定です。")

    all_asins = set()
    drops_map = {}  # asin -> priceDrops
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
        # keepaの /deal 返却は環境で2系統あるため、両方見る
        deals = (data.get("deals") or {}).get("dr") or data.get("deals") or []
        if not deals:
            print(f"[!] Page {page} returned no results. Done.")
            break

        added = 0
        for d in deals:
            asin = d.get("asin")
            if not asin:
                continue
            all_asins.add(asin)
            # ★ priceDrops（直近30日の価格ドロップ回数）を拾う
            pd = d.get("priceDrops")
            if isinstance(pd, int) and pd >= 0:
                drops_map[asin] = pd
            added += 1

        page += 1
        print(f"[+] page {page} collected {added} items (total asins={len(all_asins)})")
        time.sleep(2)

    OUT_ASINS.write_text(json.dumps(sorted(all_asins), ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_DROPS.parent.mkdir(parents=True, exist_ok=True)
    OUT_DROPS.write_text(json.dumps(drops_map, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[✓] ASINs: {len(all_asins)} → {OUT_ASINS}")
    print(f"[✓] priceDrops saved for {len(drops_map)} ASINs → {OUT_DROPS}")

if __name__ == "__main__":
    fetch_filtered_deals()
