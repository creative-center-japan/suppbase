import sqlite3
import json

INPUT_JSON = "product_details.json"
DB_FILE = "mydata.db"

def calculate_drop_rate(price_csv, window=30 * 24 * 2):
    if not price_csv or len(price_csv) < 4:
        return 0
    drops = 0
    for i in range(4, min(len(price_csv), window * 2), 2):
        prev = price_csv[i - 2]
        curr = price_csv[i]
        if curr < prev:
            drops += 1
    return drops

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    products = json.load(f)

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS products")
cur.execute("""
CREATE TABLE products (
    asin TEXT PRIMARY KEY,
    title TEXT,
    brand TEXT,
    buyBoxPrice INTEGER,
    buyBoxFallback INTEGER,
    productType INTEGER,
    lastUpdate INTEGER,
    salesRank INTEGER,
    categories TEXT,
    dropRate INTEGER,
    dropRatePrev INTEGER,
    imageUrl TEXT
)
""")

for p in products:
    asin = p.get("asin")
    title = p.get("title")
    brand = p.get("brand")
    buyBoxPrice = p.get("buyBoxPrice")

    # 平均価格・最安価格 → 補完用価格として処理
    stats = p.get("stats", {})
    raw_avg30 = stats.get("avg30")
    raw_lowest = stats.get("lowest")

    buyBoxFallback = None
    if isinstance(raw_avg30, list) and raw_avg30:
        buyBoxFallback = raw_avg30[-1]
    elif isinstance(raw_lowest, list) and raw_lowest:
        buyBoxFallback = raw_lowest[-1]

    productType = p.get("productType")
    lastUpdate = p.get("lastUpdate")
    salesRank = p.get("salesRanks", {}).get("0", [None])[-1] if "salesRanks" in p else None

    # カテゴリー文字列化（listチェック付き）
    raw_categories = p.get("categories")
    if isinstance(raw_categories, list):
        categories = ",".join(str(c) for c in raw_categories)
    else:
        categories = ""

    price_csv = p.get("csv", [])[0] if p.get("csv") else []
    dropRate = calculate_drop_rate(price_csv)
    dropRatePrev = 0  # 今は仮の0。前月比用に今後更新予定

    imageId = p.get("imagesCSV", "").split(",")[0]
    imageUrl = f"https://images-na.ssl-images-amazon.com/images/I/{imageId}.jpg" if imageId else ""

    cur.execute("""
        INSERT OR REPLACE INTO products (
            asin, title, brand, buyBoxPrice, buyBoxFallback, productType,
            lastUpdate, salesRank, categories, dropRate, dropRatePrev, imageUrl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        asin, title, brand, buyBoxPrice, buyBoxFallback, productType,
        lastUpdate, salesRank, categories, dropRate, dropRatePrev, imageUrl
    ))

conn.commit()
conn.close()
print("✅ SQLiteに dropRatePrev と buyBoxFallback を含めて保存完了！")
