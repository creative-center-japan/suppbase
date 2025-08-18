# scripts/fetch_keepa_supplement.py
# -*- coding: utf-8 -*-

"""
BCAA / EAA の ASIN を Keepa /deal API から収集するスクリプト
- 429(レート制限)に遭遇したら待機して自動リトライ（指数バックオフ）
- 途中再開（チェックポイントファイル）対応
- 実行時間・ページ数の上限、レビュー/評価のしきい値で絞り込み
- タイトルに "BCAA" または "EAA" を含む商品だけを採用（大分類カテゴリのブレを回避）

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
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set

import requests


KEEPA_API = "https://api.keepa.com/deal"
PAGE_SIZE = 150  # deal API の最大に近い値。レートに配慮しつつ広く拾う


DOMAIN_MAP = {
    # Keepa domain: https://keepa.com/#!discuss/t/supported-amazon-domains/40
    "jp": 5,
    "us": 1,
    "uk": 3,
    "de": 2,
    "fr": 4,
    "it": 8,
    "es": 9,
    "ca": 6,
    "mx": 11,
    "au": 12,
}


def load_checkpoint(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {"page": 0, "asins": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 旧形式の互換
        page = int(data.get("page", 0))
        asins = data.get("asins", [])
        if not isinstance(asins, list):
            asins = []
        return {"page": page, "asins": asins}
    except Exception:
        return {"page": 0, "asins": []}


def safe_dump_json(obj: Any, path: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def is_supplement_title(title: str) -> bool:
    """
    タイトルに BCAA / EAA を含むか（全角・半角・大小をざっくり許容）
    """
    if not title:
        return False
    t = title.lower()
    # 半角/全角英字の単純化（完璧ではないが多くのケースを拾える）
    t = t.replace("ｅ", "e").replace("ａ", "a").replace("ｂ", "b").replace("ｃ", "c")
    return ("bcaa" in t) or ("eaa" in t)


def call_keepa_deal(
    *,
    key: str,
    domain: int,
    page: int,
    min_rating: float,
    min_reviews: int,
    session: requests.Session,
    max_retries: int = 6,
    initial_sleep: float = 30.0,
) -> Dict[str, Any] | None:
    """
    Keepa /deal にアクセス。429 のとき指数バックオフで再試行。
    それ以外の一時エラー(>=500)も同様にリトライ。4xx(429以外)は致命とみなす。
    """
    params = {
        "key": key,
        "domain": domain,
        "page": page,
        "pageSize": PAGE_SIZE,
        # タイトル検索はクエリが厳密で取り逃すことがあるため、クライアント側で判定する。
        "minRating": min_rating,
        "minReviewCount": min_reviews,
        # 並び順は売上関連のドロップやセールを優先的に見たい場合は以下も検討:
        # "sort": "salesRankDrops"  # 必要に応じてコメント解除
    }

    backoff = initial_sleep
    for attempt in range(max_retries + 1):
        try:
            r = session.get(KEEPA_API, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                # レート制限 → 待機して再試行
                print(f"[!] 429 Too Many Requests on page={page}. sleep {int(backoff)}s then retry...")
                time.sleep(backoff)
                backoff = min(backoff * 1.7, 5 * 60)  # 上限5分
                continue
            if 500 <= r.status_code < 600:
                # サーバ側一時エラー
                print(f"[!] {r.status_code} from Keepa on page={page}. sleep {int(backoff)}s then retry...")
                time.sleep(backoff)
                backoff = min(backoff * 1.7, 5 * 60)
                continue

            # それ以外の 4xx は致命エラーとみなす
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

    session = requests.Session()

    pages_done = 0
    while pages_done < args.max_pages:
        # 時間制限
        if time.time() >= deadline:
            print("[i] Reached max-minutes. Stop this run.")
            break

        # Keepa コール
        data = call_keepa_deal(
            key=api_key,
            domain=domain,
            page=current_page,
            min_rating=args.min_rating,
            min_reviews=args.min_reviews,
            session=session,
        )

        if data is None:
            # 致命エラー or リトライ尽きた
            print("[!] Stop due to error (details above). Checkpoint saved.")
            # セーブして終了（次回再開）
            safe_dump_json({"page": current_page, "asins": sorted(list(collected))}, args.checkpoint)
            break

        # deal レスポンスから商品配列を取得（keepaの仕様では "deals" 配列）
        deals = data.get("deals") or []
        if not deals:
            print(f"[i] No deals at page={current_page}. Likely end.")
            # 末尾まで来た可能性 → 保存して終了
            safe_dump_json({"page": current_page, "asins": sorted(list(collected))}, args.checkpoint)
            break

        added = 0
        for d in deals:
            # 商品情報は "asin" と "title" が基本。見つからなければスキップ。
            asin = d.get("asin")
            title = d.get("title") or ""
            if not asin:
                continue

            # BCAA/EAA をタイトルで抽出（カテゴリばらつき対策）
            if is_supplement_title(title):
                if asin not in collected:
                    collected.add(asin)
                    added += 1

        print(f"[+] page={current_page} → added {added}, total={len(collected)}")

        # 進捗保存（毎ページ）
        safe_dump_json({"page": current_page + 1, "asins": sorted(list(collected))}, args.checkpoint)

        # 次ページへ
        current_page += 1
        pages_done += 1

        # レート配慮の小休止（429が出やすい環境では増やす）
        time.sleep(1.0)

    duration = int(time.time() - started)
    print(f"[✓] Done. ASINs collected: {len(collected)} / pages processed: {pages_done} / {duration}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
