# scripts/fetch_product_details_from_supabase.py

import os
import time
import requests
from supabase import create_client, Client

# =====================
# ENV
# =====================
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "70"))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

KEEPA_ENDPOINT = "https://api.keepa.com/product"

# =====================
# ASIN selection logic
# =====================

def fetch_target_asins():
    """
    Priority:
    1. BCAA / EAA (snapshot < 20)
    2. Young ASINs (snapshot 1–10)
    3. Safety fill (snapshot < 30)
    """
    asins: list[str] = []

    # ---------- ① BCAA / EAA 最優先 ----------
    bcaa_sql = """
        select p.asin
        from products p
        left join product_snapshots s on s.asin = p.asin
        where p.protein_type = 'supplement'
          and (p.title ilike '%BCAA%' or p.title ilike '%EAA%')
        group by p.asin
        having count(s.id) < 20
        order by count(s.id) asc
        limit 30;
    """
    bcaa = supabase.rpc("execute_sql", {"query": bcaa_sql}).execute().data or []
    asins.extend([r["asin"] for r in bcaa])

    # ---------- ② 若手 ASIN ----------
    young_sql = """
        select p.asin
        from products p
        left join product_snapshots s on s.asin = p.asin
        group by p.asin
        having count(s.id) between 1 and 10
        order by count(s.id) asc
        limit 30;
    """
    young = supabase.rpc("execute_sql", {"query": young_sql}).execute().data or []
    asins.extend([r["asin"] for r in young])

    # ---------- ③ 保険枠（深掘りしすぎ防止） ----------
    rest = MAX_PER_RUN - len(asins)
    if rest > 0:
        safety_sql = f"""
            select p.asin
            from products p
            left join product_snapshots s on s.asin = p.asin
            group by p.asin
            having count(s.id) < 30
            order by count(s.id) asc
            limit {rest};
        """
        safety = supabase.rpc("execute_sql", {"query": safety_sql}).execute().data or []
        asins.extend([r["asin"] for r in safety])

    # 重複排除 & 上限
    return list(dict.fromkeys(asins))[:MAX_PER_RUN]

# =====================
# Keepa fetch
# =====================

def fetch_keepa_product(asin: str) -> dict | None:
    params = {
        "key": KEEPA_API_KEY,
        "domain": 5,  # Amazon JP
        "asin": asin,
        "stats": 1,
        "offers": 20,
    }
    r = requests.get(KEEPA_ENDPOINT, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    products = data.get("products", [])
    return products[0] if products else None

# =====================
# Main
# =====================

def main():
    asins = fetch_target_asins()
    print(f"[INFO] ASINs selected: {len(asins)}")

    for asin in asins:
        try:
            product = fetch_keepa_product(asin)
            if not product:
                continue

            stats = product.get("stats", {})

            snapshot = {
                "asin": asin,
                "buybox_price": stats.get("buyBoxPrice"),
                "sales_rank_latest": stats.get("salesRank"),
                "sales_rank_drops30": stats.get("salesRankDrops30"),
                "sales_rank_drops90": stats.get("salesRankDrops90"),
                "sales_rank_drops180": stats.get("salesRankDrops180"),
                "review_count": product.get("reviews"),
            }

            supabase.table("product_snapshots").insert(snapshot).execute()

            supabase.table("products").update(
                {"updated_at": "now()"}
            ).eq("asin", asin).execute()

            time.sleep(1.2)  # Keepa safe interval

        except Exception as e:
            print(f"[ERROR] {asin}: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
