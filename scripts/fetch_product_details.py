# scripts/fetch_product_details.py
import os, json, time, requests
from typing import List, Dict, Any

API_KEY = os.environ.get("KEEPA_API_KEY", "")
DOMAIN_ID = 5  # Amazon JP

ASIN_LIST_FILE = os.environ.get("ASIN_LIST_FILE", "protein_asins_deals_filtered.json")
OUT_PRODUCT = os.environ.get("OUT_PRODUCT", "product_details.json")

KEEPA_PRODUCT_URL = "https://api.keepa.com/product"

def chunk(lst: List[str], size: int) -> List[List[str]]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def image_url_from_csv(csv: str | None) -> str | None:
    if not csv:
        return None
    img_id = csv.split(",")[0]
    return f"https://images-na.ssl-images-amazon.com/images/I/{img_id}._AC_SX679_.jpg"

def map_product(p: Dict[str, Any]) -> Dict[str, Any]:
    stats = p.get("stats") or {}
    buy_box_price = stats.get("buyBoxPrice")
    if isinstance(buy_box_price, (int, float)) and buy_box_price < 0:
        buy_box_price = None

    sales_rank = p.get("salesRank")
    if sales_rank is None:
        ranks = (p.get("salesRanks") or {}).get("0")
        if isinstance(ranks, list) and ranks:
            sales_rank = ranks[-1]

    return {
        "asin": p.get("asin"),
        "title": p.get("title") or "Unknown",
        "brand": p.get("brand"),
        "buyBoxPrice": buy_box_price,          # 表示側で/100円換算
        "buyBoxFallback": None,
        "salesRank": sales_rank,
        "dropRate": None,                      # ここでは未算出
        "dropRatePrev": None,
        "imageUrl": image_url_from_csv(p.get("imagesCSV")),
        "rating": stats.get("rating"),
        "reviewCount": stats.get("reviewCount"),
    }

def fetch_products(asins: List[str]) -> List[Dict[str, Any]]:
    if not API_KEY:
        raise RuntimeError("KEEPA_API_KEY が未設定です。")
    results: List[Dict[str, Any]] = []
    for group in chunk(asins, 100):  # Keepaは最大100ASIN/req
        params = {
            "key": API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(group),
            "history": 0,   # 軽量化
            "rating": 1,    # ★ レビュー系を返す
            "stats": 1,     # ★ buyBoxPrice / rating / reviewCount
            "buybox": 1,    # （保険）
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
        json.dump(products, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
