import json
import psycopg2

# === 入力ファイル ===
INPUT_FILES = [
    "product_details.json",
    "supplement_product_details.json"
]

# === Neon 接続情報 ===
DATABASE_URL = "postgresql://neondb_owner:npg_ze7Z0YPKGkEa@ep-long-hat-a40jwp6b-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# === データベース接続開始 ===
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

for file_name in INPUT_FILES:
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] ファイル読み込みエラー: {file_name}: {e}")
        continue

    print(f"📦 {file_name} → {len(data)} 件 読み込み中...")

    for p in data:
        asin = p.get("asin")
        title = p.get("title")
        brand = p.get("brand")
        buyBoxPrice = p.get("buyBoxPrice")
        buyBoxFallback = p.get("buyBoxFallback")
        salesRank = p.get("salesRanks", {}).get("0", [None])[-1] if p.get("salesRanks") else None
        dropRate = 0  # 今は0固定（あとでCSV計算追加も可）
        dropRatePrev = 0
        imageId = (p.get("imagesCSV") or "").split(",")[0]
        imageUrl = f"https://images-na.ssl-images-amazon.com/images/I/{imageId}.jpg" if imageId else ""

        cur.execute("""
            INSERT INTO products
            (asin, title, brand, buyBoxPrice, buyBoxFallback, salesRank, dropRate, dropRatePrev, imageUrl)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asin) DO NOTHING
        """, (asin, title, brand, buyBoxPrice, buyBoxFallback, salesRank, dropRate, dropRatePrev, imageUrl))

# === コミット＆終了 ===
conn.commit()
conn.close()
print("✅ 全データの挿入が完了しました！")
