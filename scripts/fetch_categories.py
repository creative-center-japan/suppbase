import os
import json
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # co.jp
SEARCH_API = "https://api.keepa.com/search"

TERM = os.environ.get("CATEGORY_TERM", "プロテイン")

r = requests.get(
    SEARCH_API,
    params={
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
        "type": "category",
        "term": TERM,
    },
    timeout=60,
)

# 429は今回はスキップ（workflowを落とさない）
if r.status_code == 429:
    print("[429] rate limited on category search -> skip")
    raise SystemExit(0)

r.raise_for_status()
data = r.json()

# Keepaのsearch(category)は categories か categoryList が返る実装が混在するため両対応
candidates = data.get("categories") or data.get("categoryList") or []
print(f"[OK] category candidates: {len(candidates)}")

# ログに見えるように整形して出す
out = []
for c in candidates[:50]:
    # 返り値の形が揺れるので代表的なキーを吸収
    cat_id = c.get("catId") or c.get("categoryId") or c.get("id")
    name = c.get("name") or c.get("categoryName")
    if cat_id and name:
        out.append({"catId": cat_id, "name": name})

print(json.dumps(out, ensure_ascii=False, indent=2))
