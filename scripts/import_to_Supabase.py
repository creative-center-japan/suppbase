import os
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===============================
# products テーブルに upsert
# ===============================
def upsert_products(path: str):
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    if not rows:
        print(f"[SKIP] {path} empty")
        return

    # asin が無い行は除外
    normalized = [r for r in rows if r.get("asin")]

    if not normalized:
        print(f"[SKIP] {path} no valid product rows")
        return

    supa.table("products").upsert(
        normalized,
        on_conflict="asin"
    ).execute()

    print(f"[OK] upserted {len(normalized)} rows into products")


# ===============================
# products_price_history に insert
# ===============================
def insert_price_history(path: str):
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    if not rows:
        print(f"[SKIP] {path} empty")
        return

    normalized = []
    for r in rows:
        # price / buyboxprice のどちらかがあれば履歴に入れる
        price = r.get("price") or r.get("buyboxprice")
        if r.get("asin") and price:
            normalized.append({
                "asin": r["asin"],
                "price": price,
            })

    if not normalized:
        print(f"[SKIP] {path} no valid price rows")
        return

    supa.table("products_price_history").insert(normalized).execute()
    print(f"[OK] inserted {len(normalized)} rows into products_price_history")


# ===============================
# main
# ===============================
def main():
    # protein
    upsert_products("product_details.json")
    insert_price_history("product_details.json")

    # supplement
    upsert_products("supplement_product_details.json")
    insert_price_history("supplement_product_details.json")


if __name__ == "__main__":
    main()
