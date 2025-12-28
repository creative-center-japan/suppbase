import os
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_if_exists(path: str):
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    if not rows:
        print(f"[SKIP] {path} is empty")
        return

    supa.table("products_price_history").insert(rows).execute()
    print(f"[OK] inserted {len(rows)} rows from {path}")

def main():
    # Protein workflow 用
    insert_if_exists("product_details.json")

    # Supplement workflow 用
    insert_if_exists("supplement_product_details.json")

if __name__ == "__main__":
    main()
