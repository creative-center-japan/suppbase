#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supplements (BCAA/EAA/サプリ全般) の ASIN を Keepa から収集するツール（途中再開対応）
- 指定市場（デフォルト: jp）
- レーティング/レビュー数のしきい値でフィルタ
- 最大ページ数 / 最大実行分数で打ち切り
- 途中再開のためのチェックポイントファイル保存

出力:
  - data/supplement_asins.json  …… 収集した ASIN 配列（重複なし）
  - data/supplement_asins.progress.json …… 途中再開用の進捗
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

import requests


KEEPA_DEALS_ENDPOINT = "https://api.keepa.com/deal"   # deals API を使って母集団を集める実装
# ※既存の fetch_product_details.py / fetch_supplement_product_details.py は別途詳細を取る前提


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect supplement ASINs from Keepa deals (resume friendly)."
    )
    parser.add_argument("--market", default="jp", choices=["jp", "us", "uk", "de", "fr", "it", "es", "ca"],
                        help="Amazon marketplace (Keepa domain)")
    parser.add_argument("--min-rating", type=float, default=3.8,
                        help="最小評価（例: 3.8）")
    parser.add_argument("--min-reviews", type=int, default=40,
                        help="最小レビュー件数")
    parser.add_argument("--max-pages", type=int, default=300,
                        help="取得する最大ページ数")
    parser.add_argument("--max-minutes", type=int, default=45,
                        help="取得する最大分数（時間切れで打ち切り）")
    parser.add_argument("--page-size", type=int, default=150,
                        help="1ページあたり取得件数（Keepaの既定に依存）")
    parser.add_argument("--delay-ms", type=int, default=1200,
                        help="API呼び出し間のスリープ(ミリ秒)")
    # 出力とチェックポイントは固定ファイル名（プロジェクトとワークフローと合致させる）
    parser.add_argument("--out", type=Path, default=Path("data/supplement_asins.json"),
                        help="収集したASINを書き出すJSONファイル")
    parser.add_argument("--checkpoint", type=Path, default=Path("data/supplement_asins.progress.json"),
                        help="途中再開用チェックポイント(JSON)")
    return parser.parse_args()


def market_to_domainId(market: str) -> int:
    """
    Keepaの domainId:
      1: US, 2: GB, 3: DE, 4: FR, 5: JP, 6: CA, 8: IT, 9: ES
    """
    table = {
        "us": 1,
        "uk": 2,
        "de": 3,
        "fr": 4,
        "jp": 5,
        "ca": 6,
        "it": 8,
        "es": 9,
    }
    return table.get(market, 5)


def call_keepa_deals(api_key: str, domain_id: int, page: int, page_size: int,
                     min_rating: float, min_reviews: int) -> Dict[str, Any]:
    """
    Keepa deals API 呼び出し
    参考: https://keepa.com/#!discuss/t/deal-request/116
    検索条件は「評価・レビュー件数」など *サプリ全般* を広めに拾う。詳細抽出は詳細側でフィルタ想定。
    """
    params = {
        "key": api_key,
        "domain": domain_id,
        "page": page,
        "pageSize": page_size,
        # 評価・レビュー件数でふるいにかける
        "minRating": int(min_rating * 10),  # keepaは 0–50 (=> x10) のスケール
        "minReviewCount": min_reviews,
        # カテゴリの絞り込みはここでは広めにしておき、のちの詳細取得でBCAA/EAAなど抽出
        # 必要に応じて "categories" パラメータや "titleSearch" を追加可能。
        "includeCategories": "",  # 空 = 制限なし
    }
    resp = requests.get(KEEPA_DEALS_ENDPOINT, params=params, timeout=40)
    if resp.status_code == 429:
        raise RuntimeError("Keepa 429 (rate limited)")
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("KEEPA_API_KEY")
    if not api_key:
        print("ERROR: KEEPA_API_KEY is not set.", file=sys.stderr)
        return 2

    domain_id = market_to_domainId(args.market)

    # 既存ASIN & 既存チェックポイントの読み込み
    asin_list: List[str] = load_json(args.out, default=[])
    seen: Set[str] = set(asin_list)

    ckpt: Dict[str, Any] = load_json(args.checkpoint, default={"page": 0})
    start_page = int(ckpt.get("page", 0))

    start_ts = time.time()
    max_seconds = args.max_minutes * 60

    print(f"[i] Resume from page {start_page}, already have {len(seen)} ASINs")
    current_page = start_page

    try:
        while True:
            # 時間制限
            if time.time() - start_ts > max_seconds:
                print("[i] Time limit reached. Saving checkpoint and stop.")
                break

            if current_page >= args.max_pages:
                print("[i] Reached max pages. Saving checkpoint and stop.")
                break

            # APIコール
            try:
                data = call_keepa_deals(
                    api_key=api_key,
                    domain_id=domain_id,
                    page=current_page,
                    page_size=args.page_size,
                    min_rating=args.min_rating,
                    min_reviews=args.min_reviews,
                )
            except requests.HTTPError as e:
                print(f"[!] HTTP error: {e}", file=sys.stderr)
                # 5xxなどは少し待って継続
                time.sleep(3)
                break
            except RuntimeError as e:
                # 429 のときは中断（次回再開）
                print(f"[!] {e} — stop now and resume next time.")
                break

            deals = data.get("deals") or []
            if not deals:
                print("[i] No more deals. Stop.")
                break

            added = 0
            for d in deals:
                asin = d.get("asin")
                # タイトルやカテゴリ条件で軽く弾きたい場合はここに追加（例：protein, bcaa, eaa等）
                # ここでは広めに保持し、詳細フェーズで精査する方針
                if asin and asin not in seen:
                    seen.add(asin)
                    asin_list.append(asin)
                    added += 1

            print(f"[i] page={current_page} got={len(deals)} new={added} total={len(asin_list)}")

            # 進捗保存
            save_json(args.out, asin_list)
            ckpt["page"] = current_page + 1
            save_json(args.checkpoint, ckpt)

            # 次ページへ
            current_page += 1
            time.sleep(args.delay_ms / 1000.0)

    except KeyboardInterrupt:
        print("\n[i] Interrupted. Saving checkpoint...")
    finally:
        # 念のためラスト保存
        save_json(args.out, asin_list)
        ckpt["page"] = current_page
        save_json(args.checkpoint, ckpt)
        print(f"[✓] ASINs collected: {len(asin_list)} at page={current_page}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
