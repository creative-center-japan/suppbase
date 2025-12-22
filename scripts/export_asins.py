import os
import sys
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

# 第1引数は受け取るが、いまは使わない（将来用）
# python export_asins.py protein 30
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 30

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# ASIN を「全件対象」で取得
# -----------------------------
res = (
    supa.table("tracked_asins")
    .select("asin")
    .eq("is_active", True)
    .order("last_fetched_at", desc=False, nullsfirst=True)
    .limit(LIMIT)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

# 出力ファイル名は workflow 側と合わせる
outfile = "asins_protein.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False)

print(f"[OK] exported {len(asins)} ASINs (category ignored)")
