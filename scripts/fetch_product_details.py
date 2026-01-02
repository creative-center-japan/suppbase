import json
import os
import time
import requests

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
DOMAIN_ID = 5  # Amazon.co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

API_URL = "https://api.keepa.com/product"
HEADERS = {"User-Agent": "suppbase-fetch/1.0"}

def build_image_url(images_csv: str | None) -> str | None:
    if not images_csv:
        return None
    image_id = images_csv.split(",")[0]
    return f"https://images-na.ssl-images-amazon.com/images/I/{image_id}.jpg._AC_SX679_.jpg"

def extract_salesrank(product: dict) -> int | None:
    ranks = product.get("salesRanks")
    if not ranks:
        return None
    for _, history in ranks.items():
        if history:
            v = history[-1]
            return v if v > 0 else None
    return None

def extract_rating_reviews(product: dict):
    csv = product.get("csv")
    if not csv or len(csv) < 18:
        return None, None
    try:
        rating = csv[16][-1] / 10 if csv[16] else None
        reviews = csv[17][-1] if csv[17] else None
        return rating, reviews
    except Exception:
        return None, None

def extract_price(product: dict) -> int | None:
    stats = product.get("stats")
    if not stats:
        return None
    bb = stats.get("buyBoxPrice")
    if bb and bb > 0:
        return bb
    avg = stats.get("avg30")
    return avg if avg and avg > 0 else None

def fetch_products(asins: list[str]) -> list[dict]:
    rows = []
    BATCH = 20

    for i in range(0, len(asins), BATCH):
        batch = asins[i:i+BATCH]
        print(f"[i] fetch protein batch {i//BATCH + 1}")

        params = {
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(batch),
            "stats": 180,
            "rating": 1,
            "buybox": 1,
            "update": 0,      # ★超重要：必ず最新化
            "history": 1      # ★csv を消さない
        }

        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            print("[429] rate limited, sleep 60s")
            time.sleep(60)
            continue

        r.raise_for_status()
        data = r.json()

        for p in data.get("products", []):
            if not p.get("asin") or not p.get("title"):
                continue

            rating, reviews = extract_rating_reviews(p)

            rows.append({
                "asin": p["asin"],
                "title": p["title"],
                "brand": p.get("brand"),
                "imageurl": build_image_url(p.get("imagesCSV")),
                "price": extract_price(p),
                "salesrank": extract_salesrank(p),
                "rating": rating,
                "reviewcount": reviews,
            })

        time.sleep(2)

    return rows

def main():
    if not os.path.exists(ASIN_FILE):
        print("[SKIP] ASIN file not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    rows = fetch_products(asins)
    if not rows:
        print("[SKIP] no product rows")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(rows)} rows")

if __name__ == "__main__":
    main()
