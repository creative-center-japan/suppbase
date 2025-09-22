# import_to_Supabase.py
import os
import json
import time
from typing import Any, Dict, List
from supabase import create_client, Client

INPUT_FILES = [
    "product_details.json",
    "supplement_product_details.json",
]

def to_row(p: Dict[str, Any]) -> Dict[str, Any]:
    asin = p.get("asin")
    if not asin:
        return {}
    title = p.get("title")
    brand = p.get("brand")

    buyBoxPrice = p.get("buyBoxPrice")
    buyBoxFallback = p.get("buyBoxFallback")

    salesRank = p.get("salesRank")
    if salesRank is None:
        ranks = (p.get("salesRanks") or {}).get("0")
        if isinstance(ranks, list) and ranks:
            salesRank = ranks[-1]

    imageUrl = p.get("imageUrl")
    if not imageUrl:
        images_csv = (p.get("imagesCSV") or "")
        if images_csv:
            image_id = images_csv.split(",")[0]
            imageUrl = f"https://images-na.ssl-images-amazon.com/images/I/{image_id}.jpg"

    # ★ 追加：rating / reviewcount / score
    rating = p.get("rating")
    reviewcount = p.get("reviewCount") if "reviewCount" in p else p.get("reviewcount")
    score = p.get("score")  # 通常はNULL（後段SQLで更新）

    return {
        "asin": asin,
        "title": title,
        "brand": brand,
        "buyboxprice": buyBoxPrice,
        "buyboxfallback": buyBoxFallback,
        "salesrank": salesRank,
        "droprate": p.get("dropRate") or 0,
        "droprateprev": p.get("dropRatePrev") or 0,
        "imageurl": imageUrl or "",
        "rating": rating,
        "reviewcount": reviewcount,
        "score": score,
    }

def load_products(files: List[str]) -> List[Dict[str, Any]]:
    acc: List[Dict[str, Any]] = []
    for name in files:
        try:
            with open(name, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[i] {name}: {len(data)} records")
            if isinstance(data, list):
                acc.extend(data)
        except Exception as e:
            print(f"[!] failed to read {name}: {e}")
    rows = [r for r in (to_row(p) for p in acc) if r.get("asin")]
    dedup: Dict[str, Dict[str, Any]] = {r["asin"]: r for r in rows}
    out = list(dedup.values())
    print(f"[i] rows after normalize: {len(out)}")
    return out

def chunked(lst: List[Dict[str, Any]], size: int) -> List[List[Dict[str, Any]]]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def upsert_with_retry(tbl: Any, rows: List[Dict[str, Any]], on_conflict: str = "asin",
                      max_retries: int = 5) -> None:
    attempt = 0
    while True:
        try:
            tbl.upsert(rows, on_conflict=on_conflict).execute()
            return
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise
            sleep = min(2 * (1.7 ** (attempt - 1)), 30)
            print(f"[warn] upsert chunk failed (attempt {attempt}): {e} -> sleep {sleep:.1f}s")
            time.sleep(sleep)

def main() -> None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE が未設定です。")
    client: Client = create_client(url, key)

    rows = load_products(INPUT_FILES)
    if not rows:
        print("[i] no rows to import; exit normally")
        return

    BATCH = 1000
    total = 0
    table = client.table("products")

    for group in chunked(rows, BATCH):
        upsert_with_retry(table, group, on_conflict="asin")
        total += len(group)
        print(f"... upserted {total}/{len(rows)}")

    print("🎉 import finished")

if __name__ == "__main__":
    main()
