import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # co.jp
BESTSELLERS_API = "https://api.keepa.com/bestsellers"

OUT_FILE = "asins_protein.json"

# ここは「カテゴリID」が必要です。
# 取得した候補から固定値にするのが確実なので、環境変数で受ける設計にします。
# 例: CATEGORY_ID=xxxxx
CATEGORY_ID = os.environ.get("CATEGORY_ID")

if not CATEGORY_ID:
    # カテゴリIDが無い場合は空配列を出して正常終了（後続はSKIP）
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print("[SKIP] CATEGORY_ID not set -> wrote empty asins_protein.json")
    raise SystemExit(0)

r = requests.get(
    BESTSELLERS_API,
    params={
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
        "category": CATEGORY_ID,
        # rankAvgRange は keepa クライアント実装で存在（平均ランク範囲）。
        # 指定しない（デフォルト）でOK。
    },
    timeout=60,
)

if r.status_code == 429:
    # 429は「今回は取れない」なので、空で正常終了
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    print("[429] rate limited on bestsellers -> wrote empty asins_protein.json")
    raise SystemExit(0)

r.raise_for_status()
data = r.json()

# 返却キーは実装で揺れることがあるため両対応
# - bestSellersList.asinList
# - asinList
best = data.get("bestSellersList") or data
asins = best.get("asinList") or []

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False, indent=2)

print(f"[OK] best sellers ASINs fetched: {len(asins)} -> {OUT_FILE}")
