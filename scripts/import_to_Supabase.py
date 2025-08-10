# import_to_neonDB.py  ← Supabase用に置き換え

import os
import json
from typing import Any, Dict, List, Tuple

import psycopg2
from psycopg2.extras import execute_values

# 取り込むJSONファイル（リポジトリ直下にある想定）
INPUT_FILES = [
    "product_details.json",
    "supplement_product_details.json",
]

def load_products_from_json(files: List[str]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for file_name in files:
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"📦 {file_name}: {len(data)} 件 読み込み")
            records.extend(data)
        except Exception as e:
            print(f"[!] {file_name} の読み込みに失敗: {e}")
    return records

def to_row(p: Dict[str, Any]) -> Tuple:
    """JSON 1件 → products テーブル1行に整形"""
    asin = p.get("asin")
    title = p.get("title")
    brand = p.get("brand")

    buyBoxPrice = p.get("buyBoxPrice")
    buyBoxFallback = p.get("buyBoxFallback")

    # salesRanks: {"0": [.., 最後が最新]} の形が多い想定
    salesRank = None
    ranks = (p.get("salesRanks") or {}).get("0")
    if isinstance(ranks, list) and ranks:
        salesRank = ranks[-1]

    # いまはドロップ率は0で初期化（必要に応じて算出ロジック追加）
    dropRate = 0
    dropRatePrev = 0

    # 画像URL
    images_csv = (p.get("imagesCSV") or "")
    image_id = images_csv.split(",")[0] if images_csv else ""
    imageUrl = f"https://images-na.ssl-images-amazon.com/images/I/{image_id}.jpg" if image_id else ""

    return (
        asin,
        title,
        brand,
        buyBoxPrice,
        buyBoxFallback,
        salesRank,
        dropRate,
        dropRatePrev,
        imageUrl,
    )

def main():
    # --- 接続文字列を環境変数から取得 ---
    # 例: postgresql://postgres:SuppBase.net051Da0%21Creative-J2025%23@db.xxxxxx.supabase.co:5432/postgres
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("環境変数 DATABASE_URL が設定されていません。")

    # --- データ読み込み ---
    products = load_products_from_json(INPUT_FILES)
    rows = [to_row(p) for p in products if p.get("asin")]
    print(f"✅ 取り込み対象: {len(rows)} 件")

    if not rows:
        print("データが空のため、処理を終了します。")
        return

    # --- DB接続 ---
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Postgresは未クオート識別子を小文字化するので、テーブル/カラム名は小文字で指定
    upsert_sql = """
        INSERT INTO products
            (asin, title, brand, buyboxprice, buyboxfallback, salesrank, droprate, droprateprev, imageurl)
        VALUES %s
        ON CONFLICT (asin) DO UPDATE SET
            title = EXCLUDED.title,
            brand = EXCLUDED.brand,
            buyboxprice = EXCLUDED.buyboxprice,
            buyboxfallback = EXCLUDED.buyboxfallback,
            salesrank = EXCLUDED.salesrank,
            droprate = EXCLUDED.droprate,
            droprateprev = EXCLUDED.droprateprev,
            imageurl = EXCLUDED.imageurl
    """

    # バルク挿入（1,000件ずつ）
    BATCH = 1000
    total = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        execute_values(cur, upsert_sql, chunk)
        total += len(chunk)
        print(f"… {total}/{len(rows)} 件 反映")

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 取り込み完了!")

if __name__ == "__main__":
    main()
