#!/usr/bin/env python3
"""
fetch_keepa_supplement.py
- Keepa API からサプリメント（BCAA/EAAなど）ASINを収集
- 途中再開可能 (--checkpoint)
- 最低レビュー数・評価点数のしきい値をサポート
"""

import os
import sys
import time
import json
import argparse
import requests
from pathlib import Path

KEEPA_API = "https://api.keepa.com/query"

def fetch_asins(
    api_key: str,
    domain: str,
    out_file: Path,
    checkpoint: Path,
    max_pages: int,
    max_minutes: int,
    min_rating: float,
    min_reviews: int
):
    start_time = time.time()
    all_asins = set()

    # checkpoint があればロード
    if checkpoint.exists():
        try:
            with open(checkpoint, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_asins.update(data.get("asins", []))
            print(f"[resume] {len(all_asins)} ASINs loaded from checkpoint")
        except Exception as e:
            print(f"[warn] Failed to load checkpoint: {e}")

    # Keepa domain mapping
    DOMAIN_MAP = {
        "jp": 6,   # Japan
        "us": 1,   # US
        "uk": 2,   # UK
        "de": 3,   # Germany
        "fr": 4,   # France
    }
    domain_id = DOMAIN_MAP.get(domain, 6)

    page = 0
    while page < max_pages:
        if time.time() - start_time > max_minutes * 60:
            print("[info] Time limit reached, stopping fetch")
            break

        payload = {
            "key": api_key,
            "domain": domain_id,
            "productFinderQuery": json.dumps({
                "categories": [ 160384011 ],  # 日本向け: サプリカテゴリ (例)
                "minReviewCount": min_reviews,
                "minRating": int(min_rating * 10),  # Keepaは整数で管理 (3.8 → 38)
            }),
            "page": page,
        }

        try:
            r = requests.get(KEEPA_API, params=payload, timeout=60)
            if r.status_code == 429:
                print("[!] 429 Too Many Requests - waiting 60s")
                time.sleep(60)
                continue
            r.raise_for_status()

            data = r.json()
            asins = data.get("asinList", [])
            if not asins:
                print(f"[info] No more ASINs at page {page}")
                break

            all_asins.update(asins)
            print(f"[{page}] Retrieved: {len(asins)}, total={len(all_asins)}")

            # checkpoint 保存
            checkpoint.write_text(json.dumps({"asins": list(all_asins)}, ensure_ascii=False, indent=2))
            page += 1

            # APIトークン消費調整
            time.sleep(2)

        except Exception as e:
            print(f"[error] {e}")
            time.sleep(30)

    # 結果保存
    out_file.write_text(json.dumps({"asins": list(all_asins)}, ensure_ascii=False, indent=2))
    print(f"[done] Saved {len(all_asins)} ASINs → {out_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", default="jp", help="マーケット (jp/us/uk/de/fr)")
    parser.add_argument("--max-pages", type=int, default=300)
    parser.add_argument("--max-minutes", type=int, default=45)
    parser.add_argument("--checkpoint", type=Path, default=Path("data/asins_supplements_jp.json"))
    parser.add_argument("--out", type=Path, default=Path("supplement_asins.json"))
    parser.add_argument("--min-rating", type=float, default=3.8)
    parser.add_argument("--min-reviews", type=int, default=40)

    args = parser.parse_args()
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("Error: KEEPA_API_KEY not set")
        sys.exit(1)

    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    fetch_asins(
        api_key=api_key,
        domain=args.market,
        out_file=args.out,
        checkpoint=args.checkpoint,
        max_pages=args.max_pages,
        max_minutes=args.max_minutes,
        min_rating=args.min_rating,
        min_reviews=args.min_reviews,
    )


if __name__ == "__main__":
    main()
