# scripts/import_to_Supabase.py
import os
import json
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---- load artifacts ----
products = load_json("product_details.json")
drops = load_json("data/deal_price_drops_protein.json") if os.path.exists(
    "data/deal_price_drops_protein.json"
) else {}

now = datetime.now(timezone.utc).isoformat()

for p in products:
    asin = p["asin"]
    if not asin:
        continue

    new_drop = drops.get(asin)

    # 既存レコード取得
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
        else:
            diff = 0

    record = {
        **p,
        "droprate": new_drop,
        "droprate_prev": prev_drop,
        "droprate_diff": diff,
        "droprate_updated_at": now,
    }

    (
        supa.table("products")
        .upsert(record, on_conflict="asin")
        .execute()
    )

print("✓ import & droprate diff updated")
