#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch supplement product details from Keepa by ASIN list.
- resume with checkpoint
- limit by max-asins / max-minutes
- batching requests to Keepa API
- SAFE: empty/invalid ASIN file -> write [] and exit(0)
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
    "us": 1, "uk": 2, "de": 3, "fr": 4, "jp": 5, "ca": 6,
    "it": 8, "es": 9, "in": 10, "mx": 11, "au": 12, "ae": 13,
}

def load_json_list(path: str) -> List[str]:
    """Return list[str] from JSON file; tolerate {}, {"items":[...]}, errors -> []"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return []

def save_json(path: str, obj: Any):
    """mkdir only when dirname is non-empty; safe for files like 'x.json' in cwd"""
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
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
    if not title:  # skip invalid
        return {}
    brand = p.get("brand")
    img = None
    if isinstance(p.get("imagesCSV"), str) and p["imagesCSV"]:
        img = p["imagesCSV"].split(",")[0].strip()
    stats = p.get("stats", {}) or {}
    buybox = stats.get("buyBoxPrice")
    rating = stats.get("rating")
    reviews = stats.get("reviewCount")
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
    ap.add_argument("--asin-file", dest="asin_file", required=True, help="JSON list file of ASINs")
    ap.add_argument("--out", required=True, help="Output JSON file path")
    ap.add_argument("--checkpoint", default="data/supplement_details_progress.json")
    ap.add_argument("--max-asins", type=int, default=600)
    ap.add_argument("--max-minutes", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=100)
    args = ap.parse_args()

    key = os.getenv("KEEPA_API_KEY")
    if not key:
        print("ERROR: KEEPA_API_KEY not set", file=sys.stderr)
        return 1

    domain = MARKET_TO_DOMAIN.get(args.market.lower(), 5)

    # Load ASINs
    asins = load_json_list(args.asin_file)
    if not asins:
        print(f"[i] No ASINs found in {args.asin_file}. Skipping and writing empty result.")
        save_json(args.out, [])
        return 0

    # Load checkpoint (dict of done asins)
    done: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(args.checkpoint):
        try:
            with open(args.checkpoint, "r", encoding="utf-8") as f:
                done = json.load(f)
        except Exception:
            done = {}
    if not isinstance(done, dict):
        done = {}

    # Merge existing out
    existing: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(args.out):
        try:
            with open(args.out, "r", encoding="utf-8") as f:
                ex = json.load(f)
            if isinstance(ex, list):
                for row in ex:
                    if isinstance(row, dict) and row.get("asin"):
                        existing[row["asin"]] = row
            elif isinstance(ex, dict):
                existing = ex
        except Exception:
            pass

    deadline = datetime.utcnow() + timedelta(minutes=args.max_minutes)
    collected: Dict[str, Dict[str, Any]] = dict(existing)

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
                if not row:
                    continue
                asin = row.get("asin")
                if asin:
                    collected[asin] = row
                    done[asin] = {"ts": int(time.time())}
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            print(f"[warn] HTTP {code}, sleep 5s")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"[warn] {e}, sleep 2s")
            time.sleep(2)
            continue

        # Save progress every batch
        save_json(args.checkpoint, done)

    out_list = list(collected.values())
    save_json(args.out, out_list)
    print(f"[v] Details fetched: {len(out_list)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
