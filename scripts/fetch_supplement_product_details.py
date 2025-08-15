#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
fetch_supplement_product_details.py
- KeepaのASIN詳細を取得して JSON に保存
- 途中再開(checkpoint) / 件数・時間・バッチサイズ制限 / マーケット切替 に対応

必要な環境変数:
  - KEEPA_API_KEY
"""

import argparse, json, os, sys, time
from datetime import datetime, timedelta
from typing import List, Dict
import requests

KEEPA_ENDPOINTS = {
    "jp": "https://api.keepa.com/product",
    "us": "https://api.keepa.com/product",
    "uk": "https://api.keepa.com/product",
    "de": "https://api.keepa.com/product",
    "fr": "https://api.keepa.com/product",
    "it": "https://api.keepa.com/product",
    "es": "https://api.keepa.com/product",
}

DOMAIN_ID = {
    "us": 1, "uk": 2, "de": 3, "fr": 4, "jp": 5, "ca": 6, "it": 8, "es": 9, "in": 10, "mx": 11, "au": 12
}

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_args():
    p = argparse.ArgumentParser(description="Fetch supplement product details with resume/limits.")
    p.add_argument("--market", default="jp", choices=DOMAIN_ID.keys(), help="Amazon marketplace (domain).")
    p.add_argument("--asin-file", required=True, help="Input JSON file of ASIN array.")
    p.add_argument("--out", required=True, help="Output JSON file.")
    p.add_argument("--checkpoint", default="data/supplement_details_progress.json",
                   help="Checkpoint JSON to resume progress.")
    p.add_argument("--max-asins", type=int, default=600, help="Max ASINs to fetch in this run.")
    p.add_argument("--max-minutes", type=int, default=40, help="Time budget (minutes).")
    p.add_argument("--batch-size", type=int, default=100, help="Batch size per Keepa call (<=100推奨).")
    return p.parse_args()

def keepa_fetch(api_key: str, market: str, asins: List[str]) -> Dict:
    params = {
        "key": api_key,
        "domain": DOMAIN_ID[market],
        "asin": ",".join(asins),
        # 必要に応じて追加のパラメータを
        "stats": 0,
    }
    r = requests.get(KEEPA_ENDPOINTS[market], params=params, timeout=60)
    # 429 等のレート制限は上位でリトライ
    r.raise_for_status()
    return r.json()

def main():
    args = parse_args()
    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    all_asins: List[str] = load_json(args.asin_file, [])
    if not isinstance(all_asins, list) or not all_asins:
        print(f"ERROR: ASIN file empty or invalid: {args.asin_file}", file=sys.stderr)
        sys.exit(1)

    # チェックポイント
    cp = load_json(args.checkpoint, {"done": [], "failed": []})
    done = set(cp.get("done", []))
    failed = set(cp.get("failed", []))

    # 既に完了/失敗を除外
    pending = [a for a in all_asins if a not in done and a not in failed]

    # このランで処理する上限
    if args.max_asins > 0:
        pending = pending[:args.max_asins]

    # 既存結果
    out = load_json(args.out, [])
    if not isinstance(out, list):
        out = []

    deadline = datetime.utcnow() + timedelta(minutes=args.max_minutes)
    fetched_this_run = 0

    print(f"[i] Pending: {len(pending)}  (done={len(done)}, failed={len(failed)})")
    for batch in chunk(pending, max(1, args.batch_size)):
        if datetime.utcnow() >= deadline:
            print("[i] Time budget reached. Stop this run.")
            break

        try:
            data = keepa_fetch(api_key, args.market, batch)
        except requests.HTTPError as e:
            # 429 の場合は少し待ってリトライ
            if e.response is not None and e.response.status_code == 429:
                print("[!] 429 Too Many Requests. sleep 60s and retry...")
                time.sleep(60)
                try:
                    data = keepa_fetch(api_key, args.market, batch)
                except Exception as e2:
                    print(f"[x] batch failed after retry: {e2}")
                    failed.update(batch)
                    continue
            else:
                print(f"[x] HTTP error: {e}")
                failed.update(batch)
                continue
        except Exception as e:
            print(f"[x] request failed: {e}")
            failed.update(batch)
            continue

        # Keepaレスポンス整形
        products = data.get("products", [])
        for p in products:
            asin = p.get("asin")
            if asin:
                out.append(p)
                done.add(asin)
                fetched_this_run += 1

        # 取得できなかったASINは失敗側へ
        got_asins = {p.get("asin") for p in products if p.get("asin")}
        missed = [a for a in batch if a not in got_asins]
        if missed:
            failed.update(missed)

        # こまめに保存（途中再開用）
        save_json(args.out, out)
        save_json(args.checkpoint, {"done": sorted(list(done)), "failed": sorted(list(failed))})
        print(f"[v] batch ok: +{len(products)}  total={len(out)}  done={len(done)}  failed={len(failed)}")

        # 余裕を持ってレート制御
        time.sleep(2)

    print(f"[✓] Done this run. fetched={fetched_this_run}, total_out={len(out)}, done={len(done)}, failed={len(failed)}")

if __name__ == "__main__":
    main()
