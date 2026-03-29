import json
import os
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ.get("ASIN_FILE")
CATEGORY = os.environ.get("CATEGORY")
LOCALE = os.environ.get("LOCALE", "us").lower()

if not ASIN_FILE:
    print("[ERROR][US] ASIN_FILE not set")
    raise SystemExit(1)

if not CATEGORY:
    print("[ERROR][US] CATEGORY not set")
    raise SystemExit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if not os.path.exists(ASIN_FILE):
    print(f"[ERROR][US] {ASIN_FILE} not found")
    raise SystemExit(1)

with open(ASIN_FILE, "r", encoding="utf-8") as f:
    asins = json.load(f)

if not asins:
    print("[SKIP][US] no asins")
    raise SystemExit(0)

now = datetime.now(timezone.utc).isoformat()

rows = []
seen = set()

for asin in asins:
    if not isinstance(asin, str):
        continue

    asin = asin.strip().upper()
    if not asin:
        continue

    key = (asin, LOCALE, CATEGORY)
    if key in seen:
        continue
    seen.add(key)

    rows.append(
        {
            "asin": asin,
            "category": CATEGORY,
            "locale": LOCALE,
            "first_seen_at": now,
            "last_seen_at": now,
            "is_active": True,
        }
    )

if not rows:
    print("[SKIP][US] no valid asins")
    raise SystemExit(0)

supabase.table("tracked_asins").upsert(
    rows,
    on_conflict="asin,locale,category",
).execute()

print(f"[OK][US] imported {len(rows)} asins with locale={LOCALE}, category={CATEGORY}")