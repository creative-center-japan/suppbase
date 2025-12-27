# scripts/fetch_keepa_supplement.py
# -*- coding: utf-8 -*-

"""
BCAA / EAA の ASIN を Keepa /deal API から収集するスクリプト（priceDrops 保存対応）
- 429(レート制限)に遭遇したら待機して自動リトライ（指数バックオフ）
- 途中再開（チェックポイントファイル）対応
- 実行時間・ページ数の上限、レビュー/評価のしきい値で絞り込み
- タイトルに "BCAA" または "EAA" を含む商品だけを採用（大分類カテゴリのブレを回避）
- 直近30日の価格ドロップ回数（priceDrops）を ASIN→数 の dict として保存

使い方（例：JP、最大300ページ・45分、途中再開しつつフィルタ）
  python scripts/fetch_keepa_supplement.py \
      --market jp \
      --max-pages 300 \
      --max-minutes 45 \
      --checkpoint data/asins_supplements_jp.json \
      --min-rating 3.8 \
      --min-reviews 40
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Dict, Any, List, Set
from pathlib import Path

import requests

KEEPA_API = "https://api.keepa.com/deal"
PAGE_SIZE = 150  # deal API の最大に近い値。レートに配慮しつつ広く拾う

DOMAIN_MAP = {
    "jp": 5, "us": 1, "uk": 3, "de": 2, "fr": 4, "it": 8, "es": 9, "ca": 6, "mx": 11, "au": 12,
}

def load_checkpoint(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {"page": 0, "asins": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        page = int(data.get("page", 0))
        asins = data.get("asins", [])
        if not isinstance(asins, list):
            asins = []
        return {"page": page, "asins": asins}
    except Exception:
        return {"page": 0, "asins": []}

def safe_dump_json(obj: Any, path: str) -> None:
    p = Path(path)
    if p.parent:
        p.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(p) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(p))

def is_supplement_title(title: str) -> bool:
    """
    タイトルに BCAA / EAA を含むか（全角・半角・大小をざっくり許容）
    """
    if not title:
        return False
    t = title.lower()
    t = (t.replace("ｅ", "e").replace("ａ", "a").replace("ｂ", "b")
           .replace("ｃ", "c").replace("Ａ", "a").replace("Ｂ", "b")
           .replace("Ｃ", "c").replace("Ｅ", "e"))
    return ("bcaa" in t) or ("eaa" in t)

def call_keepa_deal(
    *, key: str, domain: int, page: int, min_rating: float, min_reviews: int,
    session: requests.Session, max_retries: int = 6, initial_sleep: float = 30.0,
) -> Dict[str, Any] | None:
    """
    Keepa /deal にアクセス。429 のとき指数バックオフで再試行。
    それ以外の一時エラー(>=500)も同様にリトライ。4xx(429以外)は致命とみなす。
    """
    params = {
        "key": key, "domain": domain, "page": page, "pageSize": PAGE_SIZE,
        "minRating": min_rating, "minReviewCount": min_reviews,
    }

    backoff = initial_sleep
    for _ in range(max_retries + 1):
        try:
            r = session.get(KEEPA_API, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                # レート制限 → 待機して再試行
                try:
                    refill_in = r.json().get("refillIn", 60000)
                except Exception:
                    refill_in = int(backoff * 1000)
                sleep_s = max(refill_in / 1000, backoff)
                print(f"[!] 429 on page={page}. sleep {int(sleep_s)}s then retry...")
                time.sleep(sleep_s)
                backoff = min(backoff * 1.7, 5 * 60)  # 上限5分
                continue
            if 500 <= r.status_code < 600:
                print(f"[!] {r.status_code} on page={page}. sleep {int(backoff)}s then retry...")
                time.sleep(backoff)
                backoff = min(backoff * 1.7, 5 * 60)
                continue
            print(f"[x] HTTP {r.status_code} on page={page}: {r.text[:200]}")
            return None
        except requests.RequestException as e:
            print(f"[!] Network error on page={page}: {e}. sleep {int(backoff)}s then retry...")
            time.sleep(backoff)
            backoff = min(backoff * 1.7, 5 * 60)
    print(f"[x] Retries exhausted on page={page}.")
    return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="jp", choices=sorted(DOMAIN_MAP.keys()))
    ap.add_argument("--max-pages", type=int, default=300)
    ap.add_argument("--max-minutes", type=int, default=45)
    ap.add_argument("--checkpoint", type=str, default="data/asins_supplements_jp.json")
    ap.add_argument("--min-rating", type=float, default=3.8)
    ap.add_argument("--min-reviews", type=int, default=40)
    ap.add_argument("--drops-out", type=str, default="data/deal_price_drops_supplements.json",
                    help="ASIN→priceDrops を保存するJSONパス")
    args = ap.parse_args()

    api_key = os.getenv("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY not set")
        return 2

    domain = DOMAIN_MAP[args.market]
    started = time.time()
    deadline = started + args.max_minutes * 60.0

    # チェックポイント読み込み
    cp = load_checkpoint(args.checkpoint)
    current_page = int(cp.get("page", 0))
    collected: Set[str] = set(cp.get("asins", []))
    print(f"[i] Resume from page {current_page}, already have {len(collected)} ASINs")

    # 価格ドロップ数の復旧（ある場合）
    drops_map: Dict[str, int] = {}
    if os.path.exists(args.drops_out):
        try:
            with open(args.drops_out, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    try:
                        iv = int(v)
                        if iv >= 0:
                            drops_map[k] = iv
                    except Exception:
                        pass
            print(f"[i] loaded existing priceDrops: {len(drops_map)}")
        except Exception:
            pass

    session = requests.Session()
    pages_done = 0

    while pages_done < args.max_pages:
        # 時間制限
        if time.time() >= deadline:
            print("[i] Reached max-minutes. Stop this run.")
            break

        # Keepa コール
        data = call_keepa_deal(
            key=api_key, domain=domain, page=current_page,
            min_rating=args.min_rating, min_reviews=args.min_reviews, session=session,
        )
        if data is None:
            print("[!] Stop due to error (details above). Checkpoint saved.")
            safe_dump_json({"page": current_page, "asins": sorted(list(collected))}, args.checkpoint)
            safe_dump_json(drops_map, args.drops_out)
            break

        # レスポンスの deals 取り出し（環境により形式が2系統あるため両対応）
        deals = (data.get("deals") or {})
        if isinstance(deals, dict):
            _deals = deals.get("dr") or []
        elif isinstance(deals, list):
            _deals = deals
        else:
            _deals = []

        if not _deals:
            print(f"[i] No deals at page={current_page}. Likely end.")
            safe_dump_json({"page": current_page, "asins": sorted(list(collected))}, args.checkpoint)
            safe_dump_json(drops_map, args.drops_out)
            break

        added = 0
        for d in _deals:
            asin = d.get("asin")
            title = d.get("title") or ""
            if not asin:
                continue

            # BCAA/EAA をタイトルで抽出（カテゴリばらつき対策）
            if is_supplement_title(title):
                if asin not in collected:
                    collected.add(asin)
                    added += 1

                # ★ 直近30日の価格ドロップ回数を保存
                pd = d.get("priceDrops")
                if isinstance(pd, int) and pd >= 0:
                    drops_map[asin] = pd

        print(f"[+] page={current_page} → added {added}, total_asins={len(collected)}, drops={len(drops_map)}")

        # 進捗保存（毎ページ）
        safe_dump_json({"page": current_page + 1, "asins": sorted(list(collected))}, args.checkpoint)
        safe_dump_json(drops_map, args.drops_out)

        # 次ページへ
        current_page += 1
        pages_done += 1

        # レート配慮の小休止（429が出やすい環境では増やす）
        time.sleep(1.0)

    duration = int(time.time() - started)
    print(f"[✓] Done. ASINs={len(collected)} / pages={pages_done} / secs={duration}")
    print(f"[✓] Saved: {args.checkpoint} & {args.drops_out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
