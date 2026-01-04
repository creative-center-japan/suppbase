import os
import json
import time
import requests
from datetime import datetime, timezone

# ===============================
# 設定
# ===============================
API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp
OUT_ASIN_FILE = "asins_protein.json"

# 検索キーワード（母集団）
SEARCH_TERMS = [
    "プロテイン",
    "ホエイ プロテイン",
    "WPI プロテイン",
    "ソイ プロテイン",
]

MAX_PAGES = 5          # 1 term あたり最大 5 ページ（= 最大 50 ASIN）
SLEEP_SEC = 5          # Search API 間の待機
RATE_LIMIT_SLEEP = 60  # 429 時

SEARCH_API = "https://api.keepa.com/search"


# ===============================
# Search 実行
# ===============================
def search_asins(term: str):
    collected = []

    for page in range(MAX_PAGES):
        print(f"[i] search term='{term}' page={page}")

        while True:
            r = requests.get(
                SEARCH_API,
                params={
                    "key": API_KEY,
                    "domain": DOMAIN_ID,
                    "type": "product",
                    "term": term,
                    "page": page,
                    "stats": 180,
                    "rating": 1,     # ★ 重要：review / rating を返させる
                    "history": 0,
                    "asins-only": 1  # ★ ASIN だけ取得（軽量）
                },
                timeout=60,
            )

            if r.status_code == 429:
                print("[429] rate limited, sleep 60s")
                time.sleep(RATE_LIMIT_SLEEP)
                continue

            r.raise_for_status()
            break

        data = r.json()
        asin_list = data.get("asinList", [])

        print(f"    -> got {len(asin_list)} ASINs")

        if not asin_list:
            break

        collected.extend(asin_list)

        # Search API は軽めに間隔を空ける
        time.sleep(SLEEP_SEC)

        if len(asin_list) < 10:
            break

    return collected


# ===============================
# main
# ===============================
def main():
    all_asins = set()

    for term in SEARCH_TERMS:
        asins = search_asins(term)
        all_asins.update(asins)

    if not all_asins:
        print("[SKIP] no ASINs collected")
        return

    asin_list = sorted(all_asins)

    with open(OUT_ASIN_FILE, "w", encoding="utf-8") as f:
        json.dump(asin_list, f, ensure_ascii=False, indent=2)

    print(f"[DONE] collected {len(asin_list)} unique protein ASINs")
    print(f"       output -> {OUT_ASIN_FILE}")


if __name__ == "__main__":
    main()
