import os
import json
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

# ===============================
# 環境変数
# ===============================
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

DOMAIN_ID = 5  # JP
DEAL_URL = "https://api.keepa.com/deal"

supa = create_client(SUPABASE_URL, SUPABASE_KEY)
now = datetime.now(timezone.utc).isoformat()

# ===============================
# Web検索と同等の selection
# （あなたが貼ってくれた JSON を整理したもの）
# ===============================
BASE_SELECTION = {
    "domainId": DOMAIN_ID,
    "excludeCategories": [],
    "includeCategories": [
        3457069051,   # プロテイン
        3457070051,
        3457071051,
        3457072051,
        3457073051,
        3457074051,
        3457075051,
        3457076051,
        3457077051,
        3457079051,
    ],
    "priceTypes": [0],          # Amazon 新品
    "deltaRange": [0, 9500],
    "deltaPercentRange": [0, 2147483647],
    "salesRankRange": [-1, -1],
    "currentRange": [0, 49200],
    "minRating": -1,
    "isLowest": False,
    "isLowest90": False,
    "isLowestOffer": False,
    "isOutOfStock": False,
    "singleVariation": True,
    "hasReviews": False,
    "isPrimeExclusive": False,
    "mustHaveAmazonOffer": False,
    "mustNotHaveAmazonOffer": False,
    "sortType": 4,              # 人気順
    "dateRange": "2",           # 直近
    "warehouseConditions": [1,2,3,4,5],
    "isRangeEnabled": True,
    "isFilterEnabled": True,
    "filterErotic": True,
}

# Web検索で使っているキーワード
TITLE_KEYWORDS = [
    "プロテイン",
    "ホエイ",
    "ソイ",
    "isolate",
    "wpi",
]

MAX_PAGES = 3        # まずは 1 ページだけ
SLEEP_PER_CALL = 30  # Keepa対策

# ===============================
# API 呼び出し
# ===============================
def call_deal_api(selection):
    while True:
        r = requests.get(
            DEAL_URL,
            params={
                "key": KEEPA_API_KEY,
                "selection": json.dumps(selection, separators=(",", ":")),
            },
            timeout=60,
        )

        if r.status_code == 429:
            print("[429] deal API rate limited. sleep 60s")
            time.sleep(60)
            continue

        r.raise_for_status()
        return r.json()

# ===============================
# main
# ===============================
def main():
    total_registered = 0
    seen_asins = set()

    for keyword in TITLE_KEYWORDS:
        print(f"[i] deal search keyword='{keyword}'")

        for page in range(MAX_PAGES):
            selection = dict(BASE_SELECTION)
            selection["page"] = page
            selection["titleSearch"] = keyword

            data = call_deal_api(selection)
            deals = data.get("deals")

            if not deals:
                print("[i] no deals")
                break

            items = deals.get("dr", []) if isinstance(deals, dict) else deals
            if not items:
                break

            rows = []
            for d in items:
                asin = d.get("asin") if isinstance(d, dict) else d
                if not asin or asin in seen_asins:
                    continue

                rows.append({
                    "asin": asin,
                    "category": "protein",
                    "sub_category": "unknown",
                    "source": f"deal_search:{keyword}",
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "is_active": True,
                })
                seen_asins.add(asin)

            if rows:
                supa.table("tracked_asins").upsert(
                    rows,
                    on_conflict="asin",
                    returning="minimal"
                ).execute()
                total_registered += len(rows)
                print(f"[OK] registered {len(rows)} ASINs")

            time.sleep(SLEEP_PER_CALL)

    print(f"[DONE] total registered protein ASINs = {total_registered}")

if __name__ == "__main__":
    main()
