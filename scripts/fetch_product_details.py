import os
import json
import time
import requests
from typing import List, Dict, Any

API_KEY = os.environ.get("KEEPA_API_KEY", "")
DOMAIN_ID = 5  # Amazon JP

ASIN_LIST_FILE = os.environ.get("ASIN_LIST_FILE", "protein_asins_deals_filtered.json")
OUT_PRODUCT = os.environ.get("OUT_PRODUCT", "product_details.json")

KEEPA_PRODUCT_URL = "https://api.keepa.com/product"


# -------------------------
# utils
# -------------------------
def chunk(lst: List[str], size: int) -> List[List[str]]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def image_url_from_csv(csv: str | None) -> str | None:
    if not csv:
        return None
    img_id = csv.split(",")[0]
    return f"https://images-na.ssl-images-amazon.com/images/I/{img_id}._AC_SX679_.jpg"


def _ok_price(v) -> bool:
    return isinstance(v, int) and v > 0


def extract_price(p: Dict[str, Any]) -> tuple[int | None, str | None]:
    """
    Keepa product から価格を優先順で取得
    優先順位:
      1. BuyBox
      2. Amazon
      3. FBA 最安
      4. FBM 最安
      5. 90日平均（参考）
    """
    stats = p.get("stats") or {}

    if _ok_price(stats.get("buyBoxPrice")):
        return stats["buyBoxPrice"], "buybox"

    if _ok_price(stats.get("amazonPrice")):
        return stats["amazonPrice"], "amazon"

    if _ok_price(stats.get("lowestFBA")):
        return stats["lowestFBA"], "fba"

    if _ok_price(stats.get("lowestFBM")):
        return stats["lowestFBM"], "fbm"

    if _ok_price(stats.get("avg90")):
        return stats["avg90"], "avg90"

    return None, None


# -------------------------
# mapper
# -------------------------
def map_product(p: Dict[str, Any]) -> Dict[str, Any]:
    stats = p.get("stats") or {}

    price, price_source = extract_price(p)

    # salesRank（直値 or 履歴末尾）
    sales_rank = p.get("salesRank")
    if sales_rank is None:
        ranks = (p.get("salesRanks") or {}).get("0")
        if isinstance(ranks, list) and ranks:
            sales_rank = ranks[-1]

    return {
        "asin": p.get("asin"),
        "title": p.get("title") or "Unknown",
        "brand": p.get("brand"),
        "buyBoxPrice": price,          # ← 表示価格（フォールバック済）
        "priceSource": price_source,   # ← どの価格を使ったか（任意だが超便利）
        "salesRank": sales_rank,
        "imageUrl": image_url_from_csv(p.get("imagesCSV")),
        "rating": stats.get("rating"),
        "reviewCount": stats.get("reviewCount"),
    }


# -------------------------
# fetch
# -------------------------
def fetch_products(asins: List[str]) -> List[Dict[str, Any]]:
    if not API_KEY:
        raise RuntimeError("KEEPA_API_KEY が未設定です。")

    results: List[Dict[str, Any]] = []

    for group in chunk(asins, 100):  # Keepaは最大100 ASIN / req
        params = {
            "key": API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(group),
            "history": 0,   # 軽量化
            "rating": 1,
            "stats": 1,     # buyBox / amazon / fba / fbm / avg90 等
            "buybox": 1,
        }

        r = requests.get(KEEPA_PRODUCT_URL, params=params, timeout=60)

        if r.status_code == 429:
            try:
                refill_in = r.json().get("refillIn", 60000)
            except Exception:
                refill_in = 60000
            time.sleep(refill_in / 1000 + 1)
            continue

        r.raise_for_status()
        data = r.json()

        for p in data.get("products", []):
            results.append(map_product(p))

        time.sleep(1.5)

    return results


# -------------------------
# main
# -------------------------
def main():
    if not os.path.exists(ASIN_LIST_FILE):
        print(f"[!] ASIN list not found: {ASIN_LIST_FILE}")
        return

    with open(ASIN_LIST_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not isinstance(asins, list) or (asins and not isinstance(asins[0], str)):
        print(f"[!] Unexpected ASIN list format in {ASIN_LIST_FILE}")
        return

    print(f"[i] Fetching product details for {len(asins)} ASINs...")
    products = fetch_products(asins)
    print(f"[✓] Details fetched: {len(products)}")

    with open(OUT_PRODUCT, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
