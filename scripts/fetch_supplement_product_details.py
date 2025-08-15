#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keepa supplement product details fetcher (resume-friendly)
- 429 の refillIn に従って待機
- --max-asins / --max-minutes / --batch-size で1回の実行を短く
- --checkpoint で進捗(完了ASIN set)を保存 → 次回続きから
- 既存の出力JSON（配列）があればマージ更新（同一ASINは上書き）
"""

import os
import sys
import json
import time
import math
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

API_KEY = os.environ.get("KEEPA_API_KEY")
if not API_KEY:
    print("ERROR: KEEPA_API_KEY is not set", file=sys.stderr)
    sys.exit(1)

# Keepa domainId mapping
DOMAIN_ID = {
    "us": 1,
    "uk": 3,
    "de": 4,
    "jp": 5,
    "fr": 6,
    "it": 8,
    "es": 9,
}

# ---------- utils ----------
def load_json(path: Path, default):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def request_keepa_products(domain_id: int, asins: List[str]) -> Dict[str, Any]:
    """Keepa Product API。429はrefillInを待機して再試行。"""
    url = "https://api.keepa.com/product"
    params = {
        "key": API_KEY,
        "domain": domain_id,
        "asin": ",".join(asins),
        "buybox": 1,
        "history": 0,   # 軽量化
        "stats": 180,
    }
    while True:
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            try:
                wait_ms = r.json().get("refillIn", 60000)
            except Exception:
                wait_ms = 60000
            wait_s = wait_ms / 1000 + 1
            print(f"[429] waiting {wait_s:.1f}s ...")
            time.sleep(wait_s)
            continue
        if 500 <= r.status_code < 600:
            wait_s = 3.0
            print(f"[{r.status_code}] server error, sleep {wait_s}s ...")
            time.sleep(wait_s)
            continue
        raise RuntimeError(f"Keepa HTTP {r.status_code}: {r.text[:200]}")

def pick_first_image(product: Dict[str, Any]) -> Optional[str]:
    imgs = product.get("imagesCSV") or ""
    if imgs:
        first = imgs.split(",")[0].strip()
        if first:
            return f"https://keepa.com/!productImage?i={first}"
    return None

def map_product_row(p: Dict[str, Any]) -> Dict[str, Any]:
    """既存スキーマに合わせて整形。"""
    return {
        "asin": p.get("asin"),
        "title": p.get("title") or p.get("titleLower") or "",
        "brand": p.get("brand") or None,
        "buyboxprice": p.get("buyBoxPrice"),            # cents
        "buyboxfallback": p.get("buyBoxShipping"),      # 代替
        "salesrank": (p.get("stats") or {}).get("current", {}).get("salesRank") or p.get("salesRank"),
        "imageurl": pick_first_image(p),
    }

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="jp", choices=list(DOMAIN_ID.keys()))
    ap.add_argument("--asin-file", default="data/supplement_asins.json",
                    help="ASINリスト(JSON配列)のパス")
    ap.add_argument("--out", default="supplement_product_details.json",
                    help="出力JSON（配列）。既存があればマージ更新")
    ap.add_argument("--checkpoint", default="data/supplement_details_progress.json",
                    help="進捗(完了ASIN set)を保存するJSON")
    ap.add_argument("--batch-size", type=int, default=100,
                    help="Keepa product 呼び出し時のバッチ数（推奨≤100）")
    ap.add_argument("--max-asins", type=int, default=600,
                    help="今回処理する最大ASIN数（未処理集合から）")
    ap.add_argument("--max-minutes", type=int, default=40,
                    help="今回の最大実行分数（429待ち含む）")
    args = ap.parse_args()

    domain_id = DOMAIN_ID[args.market]

    asin_file = Path(args.asin_file)
    out_path = Path(args.out)
    ckpt_path = Path(args.checkpoint)

    asin_list = load_json(asin_file, [])
    if not isinstance(asin_list, list) or not asin_list:
        print(f"ERROR: ASIN list not found or empty: {asin_file}", file=sys.stderr)
        sys.exit(1)

    existing = load_json(out_path, [])
    details_by_asin = {row.get("asin"): row for row in existing if row.get("asin")}

    done_set = set(load_json(ckpt_path, []))

    # 未処理ASIN
    remaining = [a for a in asin_list if a not in done_set]

    if not remaining:
        print("[i] No remaining ASINs. Nothing to do.")
        print(f"[i] Details total: {len(details_by_asin)}")
        return

    if args.max_asins > 0:
        remaining = remaining[:args.max_asins]

    start = datetime.utcnow()
    processed = 0

    print(f"[i] Target ASINs this run: {len(remaining)} (file: {asin_file})")
    print(f"[i] Already done in checkpoint: {len(done_set)}")
    print(f"[i] Existing details: {len(details_by_asin)}")

    total_batches = math.ceil(len(remaining) / args.batch_size)
    for bi in range(total_batches):
        if datetime.utcnow() - start > timedelta(minutes=args.max_minutes):
            print("[i] Reached time limit. Saving and exit (resume next run).")
            break

        batch = remaining[bi*args.batch_size : (bi+1)*args.batch_size]
        if not batch:
            break

        try:
            data = request_keepa_products(domain_id, batch)
        except Exception as e:
            print(f"[!] Keepa request failed (batch {bi+1}/{total_batches}): {e}", file=sys.stderr)
            time.sleep(2)
            continue

        products = data.get("products") or []
        mapped = [map_product_row(p) for p in products if p and p.get("asin")]

        for row in mapped:
            details_by_asin[row["asin"]] = row

        processed += len(batch)
        done_set.update(batch)

        # 中間保存
        save_json(out_path, list(details_by_asin.values()))
        save_json(ckpt_path, sorted(done_set))

        print(f"[{bi+1}/{total_batches}] fetched {len(mapped)} / batch={len(batch)} "
              f"processed={processed} details_total={len(details_by_asin)}")

        time.sleep(0.8)

    # 最終保存
    save_json(out_path, list(details_by_asin.values()))
    save_json(ckpt_path, sorted(done_set))

    print(f"[✓] Done this run: processed={processed}, details_total={len(details_by_asin)}")
    print(f"[✓] Checkpoint: {ckpt_path} (done_asins={len(done_set)})")
    print(f"[✓] Output: {out_path}")

if __name__ == "__main__":
    main()
