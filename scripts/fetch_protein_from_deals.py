import os
import json
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

DOMAIN_ID = 5  # JP
DEAL_URL = "https://api.keepa.com/deal"
PRODUCT_URL = "https://api.keepa.com/product"

supa = create_client(SUPABASE_URL, SUPABASE_KEY)
now = datetime.now(timezone.utc).isoformat()

# ========= 判定ロジック =========

def has_isolate_keyword(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ["isolate", "アイソレート", "ソイレート", "wpi"])

def protein_sub_category(p):
    cats = " ".join(c.get("name", "") for c in p.get("categoryTree", []))
    title = p.get("title") or ""

    if "ソイプロテイン" in cats:
        return "soy"
    if "ホエイプロテイン" in cats:
        return "whey"
    if has_isolate_keyword(title):
        return "isolate"
    return "other"

def is_protein_target(p):
    if p.get("productType") != "PROTEIN_SUPPLEMENT_POWDER":
        return False

    cats = " ".join(c.get("name", "") for c in p.get("categoryTree", []))
    title = p.get("title") or ""

    return (
        "ソイプロテイン" in cats
        or "ホエイプロテイン" in cats
        or has_isolate_keyword(title)
    )

# ========= Keepa API =========

def fetch_deals(page: int):
    selection = {
        "page": page,
        "domainId": DOMAIN_ID,
        # 「プロテイン」配下を広めに拾う
        "includeCategories": [
            3457069051,      # プロテイン
            10504294051,     # スポーツ栄養
        ],
        "priceTypes": 3,
        "sortType": 4,
        "filterErotic": True,
        "isRangeEnabled": True,
        "isFilterEnabled": True,
    }

    r = requests.get(
        DEAL_URL,
        params={
            "key": KEEPA_API_KEY,
            "selection": json.dumps(selection, separators=(",", ":")),
        },
        timeout=60,
    )

    r.raise_for_status()
    return r.json()

def fetch_products(asins):
    r = requests.get(
        PRODUCT_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(asins),
            "stats": 0,
            "history": 0,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("products", [])

# ========= メイン =========

def main():
    collected = set()
    page = 0

    while True:
        data = fetch_deals(page)
        deals = data.get("deals")

        if not deals:
            break

        # deals は dict or list 両対応
        if isinstance(deals, dict):
            items = deals.get("dr", [])
        else:
            items = deals

        asins = []
        for d in items:
            if isinstance(d, dict):
                asin = d.get("asin")
            else:
                asin = d
            if asin:
                asins.append(asin)

        if not asins:
            break

        for i in range(0, len(asins), 50):
            batch = asins[i:i+50]
            products = fetch_products(batch)

            rows = []
            for p in products:
                if not is_protein_target(p):
                    continue

                asin = p["asin"]
                if asin in collected:
                    continue

                rows.append({
                    "asin": asin,
                    "category": "protein",
                    "sub_category": protein_sub_category(p),
                    "source": "keepa_deal",
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "is_active": True,
                })
                collected.add(asin)

            if rows:
                supa.table("tracked_asins").upsert(
                    rows,
                    on_conflict="asin",
                    returning="minimal"
                ).execute()
                print(f"[OK] registered {len(rows)} protein ASINs")

            time.sleep(30)

        page += 1
        time.sleep(5)

    print(f"[DONE] total protein ASINs: {len(collected)}")

if __name__ == "__main__":
    main()
