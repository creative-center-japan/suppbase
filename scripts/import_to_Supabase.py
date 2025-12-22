# scripts/import_to_Supabase.py
import os
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

# ここで直接読む（関数を使わない）
with open("product_details.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

insert_rows = []

for r in rows:
    if not r.get("asin"):
        continue

    insert_rows.append({
        "asin": r["asin"],
        "price": r.get("price"),
        "sales_rank": r.get("sales_rank"),
        "rating": r.get("rating"),
        "review_count": r.get("review_count"),
        "fetched_at": r["fetched_at"],
    })

if insert_rows:
    supa.table("products_price_history").insert(insert_rows).execute()

print(f"✓ inserted {len(insert_rows)} price history rows")
