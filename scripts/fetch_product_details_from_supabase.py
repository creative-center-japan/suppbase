# scripts/fetch_product_details_from_supabase.py

import os
import time
import requests
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "70"))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

KEEPA_ENDPOINT = "https://api.keepa.com/product"

# -----------------------------
# ASIN 取得ロジック（優先順）
# -----------------------------

def fetch_target_asins():
    asins = []

    # ① BCAA / EAA サプリを最優先（履歴が薄いもの）
    bcaa_sql = """
        select p.asin
        from products p
        left join product_snapshots s on s.asin = p.asin
        where p.protein_type = 'supplement'
          and (p.title ilike '%BCAA%' or p.title ilike '%EAA%')
        group by p.asin
        having count(s.id) < 10
        order by count(s.id) asc
        limit 30;
    """
    bcaa_res = supabase.rpc("execute_sql", {"query": bcaa_sql}).execute()
    asins += [r["asin"] for r in bcaa_res.data or []]

    # ② 全体で履歴が薄い ASIN
    thin_sql = """
        select p.asin
        from products p
        left join product_snapshots s on s.asin = p.asin
        group by p.asin
        having count(s.id) < 5
        order by count(s.id) asc
        limit 30;
    """
    thin_res = supabase.rpc("execute_sql", {"query": thin_sql}).execute()
    asins += [r["asin"] for r in thin_res.data or []]

    # ③ 通常ローテーション（保険）
    rest = MAX_PER_RUN - len(asins)
    if rest > 0:
        normal_res = (
            supabase.table("products")
            .select("asin")
            .order("updated_at", desc=False)
            .limit(rest)
            .execute()
        )
        asins += [r["asin"] for r in normal_res.data or []]

    # 重複除去 & 上限カット
    return list(dict.fromkeys(asins))[:MAX_PER_RUN]

# -----------------------------
# Keepa 取得
# -----------------------------

def fetch_keepa(asin):
    params = {
        "key": KEEPA_API_KEY,
        "domain": 5,  # Amazon JP
        "asin": asin,
        "stats": 1,
        "offers": 20,
    }
    r = requests.get(KEEPA_ENDPOINT, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

# -----------------------------
# メイン処理
# -----------------------------

def main():
    asins = fetch_target_asins()
    print(f"[INFO] Target ASIN count: {len(asins)}")

    for asin in asins:
        try:
            data = fetch_keepa(asin)
            products = data.get("products", [])
            if not products:
                continue

            p = products[0]
            stats = p.get("stats", {})

            snapshot = {
                "asin": asin,
                "buybox_price": stats.get("buyBoxPrice"),
                "sales_rank_latest": stats.get("salesRank"),
                "sales_rank_drops30": stats.get("salesRankDrops30"),
                "sales_rank_drops90": stats.get("salesRankDrops90"),
                "sales_rank_drops180": stats.get("salesRankDrops180"),
                "review_count": p.get("reviews"),
            }

            supabase.table("product_snapshots").insert(snapshot).execute()

            # updated_at を更新
            supabase.table("products").update(
                {"updated_at": "now()"}
            ).eq("asin", asin).execute()

            time.sleep(1.2)  # Keepa 安全待ち

        except Exception as e:
            print(f"[ERROR] {asin}: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
