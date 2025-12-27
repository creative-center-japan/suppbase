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
PRODUCT_SEARCH_URL = "https://api.keepa.com/product"

supa = create_client(SUPABASE_URL, SUPABASE_KEY)
now = datetime.now(timezone.utc).isoformat()

# ===============================
# 検索キーワード（Web検索相当）
# ===============================
TITLE_KEYWORDS = [
    "プロテイン",
    "protein",
    "ホエイ",
    "ソイ",
    "isolate",
    "wpi",
]

# ===============================
# 判定ロジック
# ===============================
def is_protein_target(p):
    if p.get("productType") != "PROTEIN_SUPPLEMENT_POWDER":
        return False

    title = (p.get("title") or "").lower()
    return any(k.lower() in title for k in TITLE_KEYWORDS)

def protein_sub_category(p):
    title = (p.get("title") or "").lower()

    if "ソイ" in title or "soy" in title:
        return "soy"
    if "ホエイ" in title or "whey" in title:
        return "whey"
    if any(k in title for k in ["isolate", "wpi", "アイソレート"]):
        return "isolate"
    return "other"

# ===============================
# Product API（429対応）
# ===============================
def fetch_products_by_keyword(keyword):
    """
    Web検索の titleSearch 相当。
    Keepaでは product API に titleSearch を含めて叩ける。
    """
    while True:
        r = requests.get(
            PRODUCT_SEARCH_URL,
            params={
                "key": KEEPA_API_KEY,
                "domain": DOMAIN_ID,
                "title": keyword,
                "stats": 1,
                "history": 0,
            },
            timeout=60,
        )

        if r.status_code == 429:
            print("[429] product search rate limited. sleep 60s")
            time.sleep(60)
            continue

        r.raise_for_status()
        return r.json().get("products", [])

# ===============================
# main
# ===============================
def main():
    total_registered = 0
    seen_asins = set()

    for keyword in TITLE_KEYWORDS:
        print(f"[i] search keyword='{keyword}'")
        products = fetch_products_by_keyword(keyword)

        rows = []
        for p in products:
            asin = p.get("asin")
            if not asin or asin in seen_asins:
                continue

            if not is_protein_target(p):
                continue

            rows.append({
                "asin": asin,
                "category": "protein",
                "sub_category": protein_sub_category(p),
                "source": f"product_search:{keyword}",
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
            print(f"[OK] keyword '{keyword}' registered {len(rows)} ASINs")

        # Web検索と同じテンポ感にする
        time.sleep(20)

    print(f"[DONE] total registered protein ASINs = {total_registered}")

if __name__ == "__main__":
    main()
