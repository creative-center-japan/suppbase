import os
import json
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

DOMAIN_ID = 5
DEAL_URL = "https://api.keepa.com/deal"
PRODUCT_URL = "https://api.keepa.com/product"

supa = create_client(SUPABASE_URL, SUPABASE_KEY)
now = datetime.now(timezone.utc).isoformat()

# ========= 制御パラメータ =========
MAX_DEAL_PAGES = 1        # ★ 1 run あたり何ページまで進むか
MAX_PRODUCT_429 = 10      # ★ product 429 が何回続いたら諦める
BASE_SLEEP = 30

# ========= 判定 =========
def has_isolate_keyword(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ["isolate", "アイソレート", "ソイレート", "wpi"])

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

# ========= API =========
def fetch_deals(page):
    selection = {
        "page": page,
        "domainId": DOMAIN_ID,
        "includeCategories": [3457069051, 10504294051],
        "priceTypes": 3,
        "sortType": 4,
        "filterErotic": True,
    }

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
            print("[429] deal API rate limited. sleep 120s")
            time.sleep(120)
            return None  # ★ deal は無理に進めない

        r.raise_for_status()
        return r.json()

def fetch_products(asins):
    product_429_count = 0

    while True:
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

        if r.status_code == 429:
            product_429_count += 1
            print(f"[429] product API rate limited ({product_429_count})")

            if product_429_count >= MAX_PRODUCT_429:
                print("[STOP] too many product 429s. stop this run.")
                return None

            time.sleep(60)
            continue

        r.raise_for_status()
        return r.json().get("products", [])

# ========= main =========
def main():
    collected = 0

    for page in range(MAX_DEAL_PAGES):
        print(f"[i] fetch deals page={page}")
        data = fetch_deals(page)
        if not data:
            break

        deals = data.get("deals")
        items = deals.get("dr", []) if isinstance(deals, dict) else deals

        asins = [
            d.get("asin") if isinstance(d, dict) else d
            for d in items if d
        ]

        print(f"[i] page {page} collected {len(asins)} ASINs")

        for i in range(0, len(asins), 50):
            batch = asins[i:i+50]
            products = fetch_products(batch)

            if products is None:
                print("[i] stop product loop")
                return

            rows = []
            for p in products:
                if not is_protein_target(p):
                    continue

                rows.append({
                    "asin": p["asin"],
                    "category": "protein",
                    "sub_category": protein_sub_category(p),
                    "source": "keepa_deal",
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "is_active": True,
                })

            if rows:
                supa.table("tracked_asins").upsert(
                    rows,
                    on_conflict="asin",
                    returning="minimal"
                ).execute()
                collected += len(rows)
                print(f"[OK] registered {len(rows)} protein ASINs")

            time.sleep(BASE_SLEEP)

    print(f"[DONE] registered {collected} protein ASINs")

if __name__ == "__main__":
    main()
