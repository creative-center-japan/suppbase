import os
import json
import time
import requests
from typing import Dict, Any, List

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
MARKET = "JP"

if not KEEPA_API_KEY:
    raise RuntimeError("KEEPA_API_KEY is not set")

KEEPA_PRODUCT_URL = "https://api.keepa.com/product"


# -------------------------------------------------
# util
# -------------------------------------------------
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


# -------------------------------------------------
# Keepa product → DB row
# -------------------------------------------------
def product_to_row(p: Dict[str, Any]) -> Dict[str, Any]:
    asin = p.get("asin")
    title = p.get("title")
    brand = p.get("brand")

    stats = p.get("stats") or {}

    # Buy Box price（負値は除外）
    buybox = safe_int(stats.get("buyBoxPrice"))
    if buybox is not None and buybox < 0:
        buybox = None

    # salesRank（直値 or 履歴末尾）
    sales_rank = safe_int(p.get("salesRank"))
    if sales_rank is None:
        ranks = (p.get("salesRanks") or {}).get("0")
        if isinstance(ranks, list) and len(ranks) > 0:
            sales_rank = safe_int(ranks[-1])

    rating = safe_float(stats.get("rating"))
    review_count = safe_int(stats.get("reviewCount"))

    image_url = None
    images = p.get("imagesCSV")
    if images:
        image_url = (
            "https://images-na.ssl-images-amazon.com/images/I/"
            + images.split(",")[0]
        )

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


# -------------------------------------------------
# main
# -------------------------------------------------
def main():
    asin_file = os.environ.get("ASIN_LIST_FILE") or "data/asins_supplements_jp.json"
    out_file = os.environ.get("OUT_PRODUCT") or "supplement_product_details.json"

    # --- load ASINs ---
    with open(asin_file, "r", encoding="utf-8") as f:
        asins_raw = json.load(f)

    # ★ dict / list 両対応（今回のエラー修正点）
    if isinstance(asins_raw, dict):
        asins = list(asins_raw.keys())
    elif isinstance(asins_raw, list):
        asins = asins_raw
    else:
        raise RuntimeError("ASIN list format is invalid")

    print(f"[INFO] ASIN count: {len(asins)}")

    rows: List[Dict[str, Any]] = []

    # Keepa product API は 100 ASIN / 1 call
    for idx, batch in enumerate(chunks(asins, 100), start=1):
        params = {
            "key": KEEPA_API_KEY,
            "domain": MARKET,
            "asin": ",".join(batch),
            "stats": 1,     # rating / reviewCount / buyBoxPrice
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
            if row.get("asin"):
                rows.append(row)

        print(
            f"[INFO] batch {idx}: fetched {len(products)} items "
            f"(total {len(rows)})"
        )

        # 下位プラン用スロットリング
        time.sleep(1.2)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[DONE] wrote {len(rows)} rows -> {out_file}")


if __name__ == "__main__":
    main()
