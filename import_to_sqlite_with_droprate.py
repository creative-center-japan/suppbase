import sqlite3
import json

INPUT_JSON_FILES = [
    "product_details.json",
    "supplement_product_details.json"
]
DB_FILE = "mydata.db"

def calculate_drop_rate(price_csv, window=30 * 24 * 2):
    if not price_csv or len(price_csv) < 4:
        return 0
    drops = 0
    for i in range(4, min(len(price_csv), window * 2), 2):
        prev_price = price_csv[i - 2]
        curr_price = price_csv[i]
        if curr_price < prev_price:
            drops += 1
    return drops

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS products")
cur.execute("""
CREATE TABLE products (
    asin TEXT PRIMARY KEY,
    title TEXT,
    brand TEXT,
    buyBoxPrice INTEGER,
    productType INTEGER,
    lastUpdate INTEGER,
    salesRank INTEGER,
    categories TEXT,
    dropRate INTEGER,
    imageUrl TEXT
)
""")

for input_file in INPUT_JSON_FILES:
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {input_file}: {e}")
        continue

    for p in products:
        asin = p.get("asin")
        title = p.get("title")
        brand = p.get("brand")
        buyBoxPrice = p.get("buyBoxPrice")
        productType = p.get("productType")
        lastUpdate = p.get("lastUpdate")
        salesRank = None
        if "salesRanks" in p and "0" in p["salesRanks"]:
            salesRank = p["salesRanks"]["0"][-1]
        categories = ",".join(str(cid) for cid in p.get("categories", []))
        price_csv = p.get("csv", [])[0] if p.get("csv") else []
        dropRate = calculate_drop_rate(price_csv)

        imageId = p.get("imagesCSV", "").split(",")[0]
        imageUrl = f"https://images-na.ssl-images-amazon.com/images/I/{imageId}.jpg" if imageId else ""

        cur.execute("""
            INSERT OR REPLACE INTO products
            (asin, title, brand, buyBoxPrice, productType, lastUpdate, salesRank, categories, dropRate, imageUrl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (asin, title, brand, buyBoxPrice, productType, lastUpdate, salesRank, categories, dropRate, imageUrl))

conn.commit()
conn.close()
print("✅ product_details + supplement データを mydata.db に保存完了！")
