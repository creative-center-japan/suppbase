import json
import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== JSON 読み込み =====
with open("asins_soy.json", "r", encoding="utf-8") as f:
    asins = json.load(f)

if not asins:
    print("[SKIP] no asins")
    raise SystemExit(0)

# ===== tracked_asins は asin のみ =====
rows = [{"asin": asin} for asin in asins]

supabase.table("tracked_asins").upsert(rows).execute()

print(f"[OK] imported {len(rows)} asins into tracked_asins")
