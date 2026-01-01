import json
import os
import time
import requests

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
DOMAIN_ID = 5  # Amazon.co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

API_URL = "https://api.keepa.com/product"

HEADERS = {
    "User-Agent": "suppbase-fetch/1.0"
}

def build_image_url(images_csv: str | None) -> str | None:
    if not images_csv:
        return None
    image_id = images_csv.split(",")[0]
    if not image_id:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{image_id}.jpg._AC_SX679_.jpg"

def extract_salesrank(product: dict) -> int | None:
    sales_ranks = product.get("salesRanks")
    if not sales_ranks:
        return None

    # Amazon.co.jp のメインカテゴリ（最初のキー）
    for _, history in sales_ranks.items():
        if isinstance(history, list) and history:
            # 最新値は末尾（Keepa仕様）
            val = history[-1]
            return val if val > 0 else None
    return None

def extract_rating_and_reviews(product: dict):
    # rating / reviewcount は csv の RATING / COUNT_REVIEWS に入る
    csv = product.get("csv")
    if not csv:
        return None, None

    # Keepa CSV index
    # 16: RATING, 17: COUNT_REVIEWS
    try:
        rating_history = csv[16]
        review_history = csv[17]

        rating = rating_history[-1] / 10 if rating_history else None
        reviews = review_history[-1] if review_history else None
        return rating, reviews
    except Exception:
        return None, None

def extract_price_from_stats(product: dict) -> int | None:
    stats = product.get("stats")
    if not stats:
        return None

    # BuyBox価格（最優先）
    bb = stats.get("buyBoxPrice")
    if bb and bb > 0:
        return bb

    # fallback: new price average
    avg = stats.get("avg30")
    if avg and avg > 0:
        return avg

    return None

def fetch_products(asins: list[str]) -> list[dict]:
    results = []

    BATCH = 20  # 安全側
    for i in range(0, len(asins), BATCH):
        batch = asins[i:i+BATCH]
        print(f"[i] fetch protein batch {i//BATCH + 1}")

        params = {
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(batch),
            "stats": 180,      # 直近180日
            "rating": 1,       # rating / review 取得
            "update": 48,      # 無駄な更新を避ける
            "history": 0       # CSV軽量化
        }

        try:
            r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                print("[429] rate limited, sleep 60s")
                time.sleep(60)
                continue

            r.raise_for_status()
            data = r.json()
            products = data.get("products", [])

            for p in products:
                asin = p.get("asin")
                title = p.get("title")

                if not asin or not title:
                    continue

                rating, reviews = extract_rating_and_reviews(p)

                row = {
                    "asin": asin,
                    "title": title,
                    "brand": p.get("brand"),
                    "imageurl": build_image_url(p.get("imagesCSV")),
                    "price": extract_price_from_stats(p),
                    "salesrank": extract_salesrank(p),
                    "rating": rating,
                    "reviewcount": reviews,
                }

                results.append(row)

            time.sleep(2)

        except Exception as e:
            print("Error:", e)
            time.sleep(30)

    return results

def main():
    if not os.path.exists(ASIN_FILE):
        print("[SKIP] asins file not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    rows = fetch_products(asins)

    if not rows:
        print("[SKIP] no valid product rows")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(rows)} rows")

if __name__ == "__main__":
    main()
