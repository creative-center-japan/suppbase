import os
import time
import random
import requests
from datetime import datetime, timezone
from supabase import create_client

# ===== ENV =====
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

# ===== Keepa 設定 =====
DOMAIN_ID = 5  # Amazon.co.jp
API_URL = "https://api.keepa.com/product"

BATCH_SIZE = 10
SLEEP_SEC = 30
MAX_ASINS_PER_RUN = 100

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_sleep(sec):
    time.sleep(sec + random.uniform(0, 3))

# ===== WPI 判定 =====
def detect_protein_type(title: str | None) -> str:
    if not title:
        return "unknown"

    t = title.lower()
    if (
        "wpi" in t
        or "アイソレート" in t
        or "isolate" in t
        or "isolated" in t
    ):
        return "wpi"

    return "other"  # ホエイ（WPC含む）

# ===== 対象 ASIN 取得 =====
res = (
    supabase.table("tracked_asins")
    .select("asin")
    .eq("is_active", True)
    .order("last_seen_at", desc=True)
    .limit(MAX_ASINS_PER_RUN)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

if not asins:
    print("[SKIP] no tracked asins")
    raise SystemExit(0)

now = datetime.now(timezone.utc).isoformat()

product_rows = []    # products 用
snapshot_rows = []   # product_snapshots 用

# ===== Keepa fetch =====
for i in range(0, len(asins), BATCH_SIZE):
    batch = asins[i:i + BATCH_SIZE]

    r = requests.get(
        API_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(batch),
            "stats": 180,
            "update": 1,
            "history": 0,
        },
        timeout=60,
    )

    if r.status_code == 429:
        print("[429] rate limited → wait 60s")
        safe_sleep(60)
        continue

    r.raise_for_status()
    products = r.json().get("products", [])

    for p in products:
        asin = p.get("asin")
        title = p.get("title")
        brand = p.get("brand")
        stats = p.get("stats") or {}

        protein_type = detect_protein_type(title)

        # --- products（マスタ＋判定結果） ---
        product_rows.append({
            "asin": asin,
            "title": title,
            "brand": brand,
            "protein_type": protein_type,
            "updated_at": now,
        })

        # --- product_snapshots（履歴・事実） ---
        snapshot_rows.append({
            "asin": asin,
            "buybox_price": stats.get("buyBoxPrice"),  # NULL OK
            "sales_rank": p.get("salesRank")
                if isinstance(p.get("salesRank"), int) else None,
            "review_count": stats.get("reviewCount"),
            "rating": stats.get("rating"),
            "captured_at": now,
        })

    safe_sleep(SLEEP_SEC)

# ===== 保存 =====
if product_rows:
    supabase.table("products").upsert(
        product_rows,
        on_conflict="asin"
    ).execute()
    print(f"[OK] upserted {len(product_rows)} products")

if snapshot_rows:
    supabase.table("product_snapshots").insert(
        snapshot_rows
    ).execute()
    print(f"[OK] inserted {len(snapshot_rows)} snapshots")

if not product_rows and not snapshot_rows:
    print("[WARN] no data saved")
