# scripts/fetch_filtered_deals.py
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple, Iterable, Optional

import requests

API_KEY = os.environ.get("KEEPA_API_KEY", "")

OUT_ASINS = Path("protein_asins_deals_filtered.json")
OUT_DROPS = Path("data/deal_price_drops_protein.json")  # asin -> priceDrops

KEEPA_DEAL = "https://api.keepa.com/deal"

# ----- Keepa /deal へ投げる selection。必要に応じて調整OK -----
SELECTION = {
    "page": 0,
    "domainId": 5,  # JP
    "includeCategories": [
        3457069051, 3457070051, 3457071051, 3457072051, 3457073051,
        3457074051, 3457076051, 3457077051, 3457079051, 10504322051,
        10504306051, 24310670051, 10504317051, 24555189051, 10504304051,
        6637456051, 16402319051, 10504302051, 10504294051
    ],
    "priceTypes": 3,
    "sortType": 4,
    "filterErotic": True,
    "isRangeEnabled": True,
    "isFilterEnabled": True
}
PAGE_SLEEP = 2.0  # 次ページへ進むときの待機（429が多ければ増やす）
MAX_RETRIES = 5


def call_keepa_deal(selection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """/deal を叩いて結果を返す。429/5xxはリトライ。"""
    if not API_KEY:
        raise RuntimeError("環境変数 KEEPA_API_KEY が未設定です。")

    backoff = 30.0
    for _ in range(MAX_RETRIES + 1):
        try:
            res = requests.get(KEEPA_DEAL, params={
                "key": API_KEY,
                "selection": json.dumps(selection, separators=(",", ":")),
            }, timeout=60)
            if res.status_code == 200:
                return res.json()
            if res.status_code == 429:
                # レート制限 → refillIn があればそれ優先
                try:
                    refill_ms = res.json().get("refillIn", int(backoff * 1000))
                except Exception:
                    refill_ms = int(backoff * 1000)
                sleep_s = max(refill_ms / 1000, backoff)
                print(f"[429] sleep {int(sleep_s)}s ...")
                time.sleep(sleep_s)
                backoff = min(backoff * 1.7, 300.0)
                continue
            if 500 <= res.status_code < 600:
                print(f"[{res.status_code}] sleep {int(backoff)}s ...")
                time.sleep(backoff)
                backoff = min(backoff * 1.7, 300.0)
                continue
            print(f"[x] HTTP {res.status_code}: {res.text[:200]}")
            return None
        except requests.RequestException as e:
            print(f"[!] Network error: {e} -> sleep {int(backoff)}s")
            time.sleep(backoff)
            backoff = min(backoff * 1.7, 300.0)
    print("[x] retries exhausted")
    return None


def iter_deals_payload(data: Dict[str, Any]) -> Iterable[Any]:
    """
    /deal の戻り形式は環境で揺れる：
      - {"deals":{"dr":[ {...}, {...} ]}} 連想配列の配列（priceDropsが取れる）
      - {"deals":[ "B000XXXX", "B00YYYY" ]} ASIN文字列の配列（priceDropsは取れない）
    どちらにも対応するため、素の要素をそのまま yield する。
    """
    deals = data.get("deals")
    if isinstance(deals, dict):
        arr = deals.get("dr") or []
        for item in arr:
            yield item
    elif isinstance(deals, list):
        for item in deals:
            yield item
    else:
        # まれに別形式のこともあるので何も返さない
        return


def extract_asin_and_price_drops(item: Any) -> Tuple[Optional[str], Optional[int]]:
    """
    item が dict なら "asin" と "priceDrops" を拾う。
    item が str なら ASIN だけ拾う（priceDrops は None）。
    不明形式は (None, None)。
    """
    if isinstance(item, dict):
        asin = item.get("asin") or item.get("asinId") or None
        pd = item.get("priceDrops")
        try:
            pd = int(pd) if pd is not None else None
        except Exception:
            pd = None
        return asin, pd
    if isinstance(item, str):
        return item, None
    return None, None


def main():
    all_asins = set()
    drops_map: Dict[str, int] = {}

    page = 0
    while True:
        sel = dict(SELECTION)
        sel["page"] = page

        data = call_keepa_deal(sel)
        if not data:
            print("[!] stop: request failed")
            break

        added = 0
        count_this_page = 0
        for raw in iter_deals_payload(data):
            count_this_page += 1
            asin, pd = extract_asin_and_price_drops(raw)
            if not asin:
                continue
            if asin not in all_asins:
                all_asins.add(asin)
                added += 1
            if pd is not None:
                drops_map[asin] = pd

        print(f"[+] page {page} collected {count_this_page} items, "
              f"added {added} (total asins={len(all_asins)}, drops={len(drops_map)})")

        # 終了条件：このページが0件、または次のページが無さそう
        if count_this_page == 0:
            break

        # 次ページへ
        page += 1
        time.sleep(PAGE_SLEEP)

    # 保存
    OUT_ASINS.write_text(json.dumps(sorted(all_asins), ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_DROPS.parent.mkdir(parents=True, exist_ok=True)
    OUT_DROPS.write_text(json.dumps(drops_map, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[✓] ASINs: {len(all_asins)} → {OUT_ASINS}")
    print(f"[✓] priceDrops entries: {len(drops_map)} → {OUT_DROPS}")


if __name__ == "__main__":
    main()
