# scripts/fetch_product_details.py
import os, json, time, requests
from typing import List, Dict, Any

API_KEY = os.environ.get("KEEPA_API_KEY", "")
DOMAIN_ID = 5  # Japan

ASIN_LIST_FILE = os.environ.get("ASIN_LIST_FILE", "protein_asins_deals_filtered.json")
OUT_PRODUCT = os.environ.get("OUT_PRODUCT", "product_details.json")
OUT_SUPP_PRODUCT = os.environ.get("OUT_SUPP_PRODUCT", "supplement_product_details.json")

KEEPA_PRODUCT_URL = "https://api.keepa.com/product"

def chunk(lst: List[str], size: int) -> List[List[str]]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def image_url_from_csv(csv: str | None) -> str | None:
    if not csv:
        return None
    # KeepaのimagesCSVはカンマ区切りの画像ID
    # 1つ目を使い、標準のS3 URLに変換
    img_id = csv.split(",")[0]
    return f"https://images-na.ssl-images-amazon.com/images/I/{img_id}._AC_SX679_.jpg"

def map_product(p: Dict[str, Any]) -> Dict[str, Any]:
    # import_to_Supabase.pyが期待するキーに寄せる
    buy_box_price = p.get("buyBoxPrice")
    if isinstance(buy_box_price, (int, float)) and buy_box_price < 0:
        buy_box_price = None

    return {
        "asin": p.get("asin"),
        "title": p.get("title") or "Unknown",
        "brand": p.get("brand"),
        "buyBoxPrice": buy_box_price,             # セント単位。import側で/100している想定
        "buyBoxFallback": None,
        "salesRank": p.get("salesRank") or None,  # 取れないこともあるので None 可
        "dropRate": None,                         # ここでは算出しない（DBの列はNULL可）
        "dropRatePrev": None,
        "imageUrl": image_url_from_csv(p.get("imagesCSV")),
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
            "history": 0,  # 軽量化（履歴は不要）
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
        time.sleep(1.5)  # APIに優しく
    return results

def main():
    if not os.path.exists(ASIN_LIST_FILE):
        print(f"[!] ASIN list not found: {ASIN_LIST_FILE}")
        return

    with open(ASIN_LIST_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    # ASIN配列以外の場合は諦める
    if not isinstance(asins, list) or (asins and not isinstance(asins[0], str)):
        print(f"[!] Unexpected ASIN list format in {ASIN_LIST_FILE}")
        return

    print(f"[i] Fetching product details for {len(asins)} ASINs...")
    products = fetch_products(asins)
    print(f"[✓] Details fetched: {len(products)}")

    with open(OUT_PRODUCT, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False)

    # サプリ専用が無ければ、とりあえず同じ内容を出力（後で条件分岐したければここで絞り込み）
    with open(OUT_SUPP_PRODUCT, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)

if __name__ == "__main__":
    main()
