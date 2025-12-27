import os, json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert(path):
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    if rows:
        supa.table("products_price_history").insert(rows).execute()
        print(f"[OK] inserted {len(rows)} rows from {path}")

insert("product_details.json")
insert("supplement_product_details.json")
