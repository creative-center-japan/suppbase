#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch supplement product details from Keepa by ASIN list.
- resume with checkpoint
- limit by max-asins / max-minutes
- batching requests to Keepa API

Usage example:
  python scripts/fetch_supplement_product_details.py \
    --market jp \
    --asin-file data/supplement_asins.json \
    --out data/supplement_product_details.json \
    --checkpoint data/supplement_details_progress.json \
    --max-asins 600 \
    --max-minutes 40 \
    --batch-size 100
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests

MARKET_TO_DOMAIN = {
    "us": 1,
    "uk": 2,
    "de": 3,
    "fr": 4,
    "jp": 5,
    "ca": 6,
    "it": 8,
    "es": 9,
    "in": 10,
    "mx": 11,
    "au": 12,
    "ae": 13,
}

def load_json_list(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # JSON が { "items":[...]} のような場合にも一応対応
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return []

def save_json(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def keepa_products(key: str, domain: int, asins: List[str]) -> Dict[str, Any]:
    url = "https://api.keepa.com/product"
    params = {
        "key": key,
        "domain": domain,
        "asin": ",".join(asins),
        "buybox": 1,
        "history": 0,
        "rating": 1,
        "stats": 1,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def product_to_row(p: Dict[str, Any]) -> Dict[str, Any]:
    asin = p.get("asin")
    title = p.get("title")
    brand = p.get("brand")
    img = None
    if isinstance(p.get("imagesCSV"), str):
        img = p["imagesCSV"].split(",")[0].strip() if p["imagesCSV"] else None

    stats = p.get("stats", {}) or {}
    buybox = stats.get("buyBoxPrice")  # Keepaの価格はセントなどの最小単位で入ることが多い
    # 日本円のときはそのまま / その他は換算が必要。ここでは生値を入れるだけにする
    rating = p.get("stats", {}).get("rating") or p.get("csv", {}).get("RATING")
    reviews = p.get("stats", {}).get("reviewCount")

    return {
        "asin": asin,
        "title": title,
        "brand": brand,
        "imageUrl": img,
        "buyBoxPrice": buybox,
        "rating": rating,
        "reviewCount": reviews,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="jp", help="jp/us/uk/... (Keepa domain)")
    ap.add_argument("--asin-file", required=True, help="JSON list file of ASINs")
    ap.add_argument("--out", required=True, help="Output JSON (append/merge)")
    ap.add_argument("--checkpoint", default="data/supplement_details_progress.json")
    ap.add_argument("--max-asins", type=int, default=600)
    ap.add_argument("--max-minutes", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=100)
    args = ap.parse_args()

    key = os.getenv("KEEPA_API_KEY")
    if not key:
        print("ERROR: KEEPA_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    domain = MARKET_TO_DOMAIN.get(args.market.lower(), 5)

    asins = load_json_list(args.asin-file if hasattr(args, "asin-file") else args.asin_file)  # type: ignore
    if not asins:
        print(f"ERROR: ASIN file empty or invalid: {args.asin_file if hasattr(args,'asin_file') else args.asin-file}", file=sys.stderr)  # type: ignore
        sys.exit(1)

    # チェックポイント（既に終えたASIN）
    done: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(args.checkpoint):
        try:
            done = json.load(open(args.checkpoint, "r", encoding="utf-8"))
        except Exception:
            done = {}
    if not isinstance(done, dict):
        done = {}

    # 既存のアウトファイルもマージ（重複保存防止）
    existing: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(args.out):
        try:
            ex = json.load(open(args.out, "r", encoding="utf-8"))
            if isinstance(ex, list):
                for row in ex:
                    if isinstance(row, dict) and row.get("asin"):
                        existing[row["asin"]] = row
            elif isinstance(ex, dict):
                existing = ex
        except Exception:
            pass

    deadline = datetime.utcnow() + timedelta(minutes=args.max_minutes)
    picked = 0
    collected: Dict[str, Dict[str, Any]] = {}
    collected.update(existing)  # 既存分も温存

    # 未処理 ASIN に限定
    target = [a for a in asins if a not in done and a not in collected]
    if args.max_asins and len(target) > args.max_asins:
        target = target[: args.max_asins]

    print(f"[i] Fetching product details for {len(target)} ASINs...")

    i = 0
    while i < len(target):
        if datetime.utcnow() > deadline:
            print("[!] Max minutes reached, stopping early.")
            break

        chunk = target[i : i + args.batch_size]
        i += args.batch_size

        try:
            res = keepa_products(key, domain, chunk)
            prods = res.get("products") or []
            for p in prods:
                row = product_to_row(p)
                asin = row.get("asin")
                if asin:
                    collected[asin] = row
                    done[asin] = {"ts": int(time.time())}
        except requests.HTTPError as e:
            # Rate limit 等：軽く待って続行
            print(f"[warn] HTTP {e.response.status_code if e.response else ''}, sleep 5s")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"[warn] {e}, sleep 2s")
            time.sleep(2)
            continue

        # 進捗のスナップショット
        save_json(args.checkpoint, done)

    # 出力は list に整形
    out_list = list(collected.values())
    save_json(args.out, out_list)
    print(f"[v] Details fetched: {len(out_list)}")

if __name__ == "__main__":
    main()
