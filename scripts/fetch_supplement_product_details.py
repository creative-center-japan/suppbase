import os
import json
import time
import requests
from typing import Dict, Any, List

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
MARKET = "JP"

# Keepa API
KEEPA_PRODUCT_URL = "https://api.keepa.com/product"

# ---- util -------------------------------------------------

def chunks(lst: List[str], n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

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

# ---- Keepa product -> row --------------------------------

def product_to_row(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keepa product 1件 → Supabase products 1行
    下位プラン前提で取れるものは全部取る
    """

    asin = p.get("asin")
    title = p.get("title")
    brand = p.get("brand")

    stats = p.get("stats") or {}

    # ---- buyBoxPrice（負値は NULL）----
    buybox = safe_int(stats.get("buyBoxPrice"))
    if buybox is not None and buybox < 0:
        buybox = None

    # ---- salesRank（直値 or salesRanks 末尾）----
    sales_rank = safe_int(p.get("salesRank"))
    if sales_rank is None:
        ranks = (p.get("salesRanks") or {}).get("0")
        if isinstance(ranks, list) and len(ranks) > 0:
            sales_rank = safe_int(ranks[-1])

    # ---- rating / reviewCount ----
    rating = safe_float(stats.get("rating"))
    review_count = safe_int(stats.get("reviewCount"))

    # ---- image ----
    image_url = None
    images = p.get("imagesCSV")
    if images:
        image_url = "https://images-na.ssl-images-amazon.com/images/I/" + images.split(",")[0]

    return {
        "asin": asin,
        "title": title,
        "brand": brand,
        "buyBoxPrice": buybox,
        "salesRank": sales_rank,
        "rating": rating,
        "reviewCount": review_count,
        "imageUrl": image_url,
    }

# ---- main -------------------------------------------------

def main():
    asin_file = os.environ.get("ASIN_LIST_FILE") or "data/asins_supplements_jp.json"
    out_file = os.environ.get("OUT_PRODUCT") or "supplement_product_details.json"

    with open(asin_file, "r", encoding="utf-8") as f:
        asins = json.load(f)

    print(f"[INFO] ASIN count: {len(asins)}")

    rows: List[Dict[str, Any]] = []

    # Keepa は 100 ASIN / 1 call
    for idx, batch in enumerate(chunks(asins, 100), start=1):
        params = {
            "key": KEEPA_API_KEY,
            "domain": MARKET,
            "asin": ",".join(batch),
            "stats": 1,        # ★ rating / reviewCount / buyBoxPrice
            "buybox": 1,
            "offers": 0,
            "history": 0,
        }

        try:
            r = requests.get(KEEPA_PRODUCT_URL, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[WARN] batch {idx} failed: {e}")
            time.sleep(2)
            continue

        products = data.get("products") or []
        for p in products:
            row = product_to_row(p)
            if not row.get("asin"):
                continue
            rows.append(row)

        print(f"[INFO] batch {idx}: fetched {len(products)} items (total {len(rows)})")
        time.sleep(1.2)  # 下位プラン用スロットル

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[DONE] wrote {len(rows)} rows -> {out_file}")

if __name__ == "__main__":
    main()
