# scripts/fetch_product_details.py
import os, json, time, requests
from typing import List, Dict, Any

API_KEY = os.environ.get("KEEPA_API_KEY", "")
DOMAIN_ID = 5  # Japan

ASIN_LIST_FILE = os.environ.get("ASIN_LIST_FILE", "protein_asins_deals_filtered.json")
OUT_PRODUCT = os.environ.get("OUT_PRODUCT", "product_details.json")
# サプリ用の出力はこのスクリプトでは触らない（空配列で上書きしない）
# OUT_SUPP_PRODUCT は別スクリプト(fetch_supplement_product_details.py)で生成する想定

KEEPA_PRODUCT_URL = "https://api.keepa.com/product"

def chunk(lst: List[str], size: int) -> List[List[str]]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def image_url_from_csv(csv: str | None) -> str | None:
    if not csv:
        return None
    img_id = csv.split(",")[0]
    return f"https://images-na.ssl-images-amazon.com/images/I/{img_id}._AC_SX679_.jpg"

def map_product(p: Dict[str, Any]) -> Dict[str, Any]:
    # Keepaの stats 内に buyBoxPrice / rating / reviewCount が入る
    stats = p.get("stats") or {}
    buy_box_price = stats.get("buyBoxPrice")
    if isinstance(buy_box_price, (int, float)) and buy_box_price < 0:
        buy_box_price = None

    # salesRank は product直下にもあるが、なければ stats から適宜拾う
    sales_rank = p.get("salesRank")
    if sales_rank is None:
        sales_rank = (p.get("salesRanks") or {}).get("0")
        if isinstance(sales_rank, list) and sales_rank:
            sales_rank = sales_rank[-1]

    return {
        "asin": p.get("asin"),
        "title": p.get("title") or "Unknown",
        "brand": p.get("brand"),
        "buyBoxPrice": buy_box_price,          # /100 で円表示する想定
        "buyBoxFallback": None,
        "salesRank": sales_rank,
        "dropRate": None,                      # ここでは算出しない
        "dropRatePrev": None,
        "imageUrl": image_url_from_csv(p.get("imagesCSV")),
        "rating": stats.get("rating"),
        "reviewCount": stats.get("reviewCount"),
    }

def fetch_products(asins: List[str]) -> List[Dict[str, Any]]:
    if not API_KEY:
        raise RuntimeError("KEEPA_API_KEY が未設定です。")

    results: List[Dict[str, Any]] = []
    for group in chunk(asins, 100):  # Keepaは最大100ASIN/リクエスト
        params = {
            "key": API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(group),
            "history": 0,   # 軽量化
            "rating": 1,    # ★ 追加
            "stats": 1,     # ★ 追加（buyBoxPrice / rating / reviewCount を得る）
            "buybox": 1,    # 任意（buyBoxPriceを統一的に得たい場合）
        }
        r = requests.get(KEEPA_PRODUCT_URL, params=params, timeout=60)
        if r.status_code == 429:
            # レート制限
            try:
                refill_in = r.json().get("refillIn", 60000)
            except Exception:
                refill_in = 60000
            time.sleep(refill_in / 1000 + 1)
            continue
        r.raise_for_status()
        data = r.json()
        prods = data.get("products", [])
        for p in prods:
            results.append(map_product(p))
        time.sleep(1.5)  # APIにやさしく
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
