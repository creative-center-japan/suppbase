import os, json, time, requests
from datetime import datetime, timezone

API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

def safe_int(v):
    return v if isinstance(v, int) and v > 0 else None

def main():
    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    rows = []

    for i in range(0, len(asins), 50):
        batch = asins[i:i+50]

        r = requests.get(
            "https://api.keepa.com/product",
            params={
                "key": API_KEY,
                "domain": DOMAIN_ID,
                "asin": ",".join(batch),
                "stats": 1,
                "history": 0,
            },
            timeout=60,
        )
        r.raise_for_status()

        for p in r.json().get("products", []):
            stats = p.get("stats") or {}
            rows.append({
                "asin": p["asin"],
                "price": safe_int(stats.get("buyBoxPrice")) or safe_int(stats.get("avg90")),
                "sales_rank": safe_int(p.get("salesRank")),
                "rating": stats.get("rating"),
                "review_count": stats.get("reviewCount"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        time.sleep(30)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(rows)} rows")

if __name__ == "__main__":
    main()
