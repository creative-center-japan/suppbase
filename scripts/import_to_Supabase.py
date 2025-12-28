import os
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        # products_price_history に入れるのはこれだけ
        if r.get("asin") and r.get("price"):
            normalized.append({
                "asin": r["asin"],
                "price": r["price"],
            })

    if not normalized:
        print(f"[SKIP] {path} no valid price rows")
        return

    supa.table("products_price_history").insert(normalized).execute()
    print(f"[OK] inserted {len(normalized)} rows from {path}")

def main():
    # protein
    insert_price_history("product_details.json")

    # supplement
    insert_price_history("supplement_product_details.json")

if __name__ == "__main__":
    main()
