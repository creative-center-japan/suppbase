import os
import json
from supabase import create_client
from typing import Dict, Any, List

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.environ.get("SUPABASE_SERVICE_ROLE")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE is not set")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# ==== 入力ファイル ====
PRODUCT_FILES = [
    "product_details.json",
    "supplement_product_details.json",
]

# price drop ファイル（存在すれば使用）
DROPS_FILES = [
    "data/deal_price_drops_protein.json",
    "data/deal_price_drops_supplements.json",
]


# -------------------------------------------------
# util
# -------------------------------------------------
def load_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_int(v):
    try:
        if v is None:
            return None
        v = int(v)
        return v if v >= 0 else None
    except Exception:
        return None


def safe_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


# -------------------------------------------------
# load priceDrops
# -------------------------------------------------
drop_map: Dict[str, int] = {}

for f in DROPS_FILES:
    data = load_json(f)
    if not isinstance(data, list):
        continue
    for r in data:
        asin = r.get("asin")
        drops = r.get("priceDrops")
        if asin and isinstance(drops, int):
            drop_map[asin] = drops

print(f"[INFO] priceDrops loaded: {len(drop_map)} items")


# -------------------------------------------------
# load products
# -------------------------------------------------
rows: List[Dict[str, Any]] = []

for f in PRODUCT_FILES:
    data = load_json(f)
    if not isinstance(data, list):
        continue
    rows.extend(data)

print(f"[INFO] product rows loaded: {len(rows)}")


# -------------------------------------------------
# upsert
# -------------------------------------------------
upserted = 0

for r in rows:
    asin = r.get("asin")
    if not asin:
        continue

    payload = {
        # 必須
        "asin": asin,
        "title": r.get("title"),
        "brand": r.get("brand"),

        # 価格
        "buyboxprice": safe_int(r.get("buyBoxPrice")),
        "buyboxfallback": None,

        # ★ ここが重要（今まで入ってなかった）
        "salesrank": safe_int(r.get("salesRank")),
        "rating": safe_float(r.get("rating")),
        "reviewcount": safe_int(r.get("reviewCount")),

        # price drop
        "droprate": drop_map.get(asin, 0),
        "droprateprev": 0,

        # image
        "imageurl": r.get("imageUrl"),
    }

    # 空データで上書きしない
    payload = {k: v for k, v in payload.items() if v is not None}

    supabase.table("products").upsert(payload).execute()
    upserted += 1

print(f"[DONE] upserted rows: {upserted}")
