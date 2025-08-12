#!/usr/bin/env python3
import os, json, time, random, argparse, pathlib, sys
import requests
from datetime import datetime, timedelta

# ■ APIキーは環境変数から
API_KEY = os.environ.get("KEEPA_API_KEY")
if not API_KEY:
    print("ERROR: 環境変数 KEEPA_API_KEY が未設定です。GitHub Actions の Secrets に設定してください。", file=sys.stderr)
    sys.exit(1)

# ■ マーケット（今回はJPのみ。増やすなら dict を広げる）
DOMAIN_ID = {"jp": 5}

# ■ 「サプリ（BCAA/EAA）」に寄せたJPカテゴリ
JP_SUPP_CATS = [
    3457080051, 169903011, 169904011, 169905011,
    169909011, 169911011, 3457085051, 3457084051
]

def title_is_supplement(title: str) -> bool:
    """BCAA/EAA などの簡易フィルタ。不要なら True 固定でもOK。"""
    if not title:
        return False
    t = title.lower()
    return any(k in t for k in ["bcaa", "eaa", "アミノ", "アミノ酸"])

def save_checkpoint(path: pathlib.Path, asins_set: set):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(asins_set), f, ensure_ascii=False, indent=2)

def load_checkpoint(path: pathlib.Path) -> set:
    if path.exists():
        try:
            return set(json.load(open(path, encoding="utf-8")))
        except Exception:
            return set()
    return set()

def fetch_page(selection: dict, max_retry: int = 6) -> dict:
    """429 は refillIn に従って待機。5xx は指数バックオフ。"""
    url = "https://api.keepa.com/deal"
    params = {"key": API_KEY, "selection": json.dumps(selection)}
    retry = 0
    while True:
        r = requests.get(url, params=params, timeout=60)
        # 429: レート制限 → refillIn(ms) + α 待つ
        if r.status_code == 429:
            try:
                refill_ms = r.json().get("refillIn", 60000)
            except Exception:
                refill_ms = 60000
            wait_s = refill_ms / 1000 + 1 + random.uniform(0, 1)
            print(f"[429] wait {wait_s:.1f}s")
            time.sleep(wait_s)
            continue
        # 一時エラー（Keepa は 500 が出ることあり）
        if r.status_code >= 500:
            if retry >= max_retry:
                raise RuntimeError(f"Keepa 5xx {r.status_code}")
            backoff = (2 ** retry) + random.uniform(0, 0.5)
            print(f"[{r.status_code}] retry in {backoff:.1f}s (#{retry+1})")
            time.sleep(backoff)
            retry += 1
            continue
        # その他エラー
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="jp", choices=list(DOMAIN_ID.keys()))
    ap.add_argument("--max-pages", type=int, default=200, help="この実行で巡回する最大ページ数")
    ap.add_argument("--max-minutes", type=int, default=45, help="この実行の上限時間（分）")
    ap.add_argument("--checkpoint", default="data/asins_supplements_{market}.json", help="保存ファイルパス（{market} 可）")
    ap.add_argument("--min-rating", type=float, default=3.5, help="レビュー平均の下限（粗いフィルタ）")
    ap.add_argument("--min-reviews", type=int, default=20, help="レビュー件数の下限（粗いフィルタ）")
    args = ap.parse_args()

    domain_id = DOMAIN_ID[args.market]
    out_path = pathlib.Path(args.checkpoint.format(market=args.market))
    asins = load_checkpoint(out_path)
    print(f"[i] checkpoint: {len(asins)} 件読み込み")

    start = datetime.utcnow()
    page = 0
    save_every = 150  # 150件刻みでセーブ

    while page < args.max_pages:
        # 時間上限（Actionsが切れても再開できるよう、短めで切る）
        if datetime.utcnow() - start > timedelta(minutes=args.max_minutes):
            print("[i] 時間上限に達したため中断（次回再開）")
            break

        selection = {
            "page": page,
            "domainId": domain_id,
            "includeCategories": JP_SUPP_CATS,
            "priceTypes": 3,
            "sortType": 4,           # ランキング順
            "filterErotic": True,
            "isRangeEnabled": True,
            "isFilterEnabled": True,

            # 取得を絞って429を抑える（Keepaの deal selection による粗フィルタ）
            "minRating": args.min_rating,
            "minReviewCount": args.min_reviews
        }

        try:
            data = fetch_page(selection)
        except Exception as e:
            print(f"[!] fetch_page error: {e}")
            time.sleep(15)
            page += 1
            continue

        deals = data.get("deals", {}).get("dr", [])
        if not deals:
            print(f"[i] page={page}: no results → stop")
            break

        added = 0
        for d in deals:
            asin = d.get("asin")
            title = (d.get("title") or d.get("titleShort") or "")
            if not asin:
                continue
            # BCAA/EAA に寄せたい時：タイトルで最終フィルタ
            if not title_is_supplement(title):
                continue
            if asin not in asins:
                asins.add(asin)
                added += 1

        print(f"[{page}] +{added} / total {len(asins)}")

        # 進捗セーブ（定期）
        if added > 0 and len(asins) % save_every < 10:
            save_checkpoint(out_path, asins)
            print(f"[✓] checkpoint saved: {out_path} ({len(asins)})")

        # 次ページへ（429防止のゆるい間隔 + ジッター）
        time.sleep(1.2 + random.uniform(0, 0.6))
        page += 1

    # 最終保存
    save_checkpoint(out_path, asins)
    print(f"[✓] 完了: {len(asins)} 件 → {out_path}")

if __name__ == "__main__":
    main()
