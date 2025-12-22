# scripts/import_to_Supabase.py
import os
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# ---- load artifacts ----
products = load_json("product_details.json")
drops = load_json("data/deal_price_drops_protein.json") if os.path.exists(
    "data/deal_price_drops_protein.json"
) else {}

now = datetime.now(timezone.utc).isoformat()

# DBに存在するカラムだけを明示的に送る
ALLOWED_KEYS = {
    "asin",
    "title",
    "brand",
    "buyBoxPrice",
    "salesRank",
    "rating",
    "reviewCount",
    "imageUrl",
}

for p in products:
    asin = p.get("asin")
    if not asin:
        continue

    new_drop = drops.get(asin)

    # 既存 droprate を取得
    res = (
        supa.table("products")
        .select("droprate")
        .eq("asin", asin)
        .limit(1)
        .execute()
    )

    prev_drop = None
    if res.data:
        prev_drop = res.data[0].get("droprate")

    diff = 0
    if new_drop is not None:
        if prev_drop is not None:
            diff = max(new_drop - prev_drop, 0)

    record = {
        k: v for k, v in p.items() if k in ALLOWED_KEYS
    }

    record.update({
        "droprate": new_drop,
        "droprate_prev": prev_drop,
        "droprate_diff": diff,
        "droprate_updated_at": now,
    })

    (
        supa.table("products")
        .upsert(record, on_conflict="asin")
        .execute()
    )

print("✓ import & droprate diff updated")
