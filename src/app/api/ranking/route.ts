// suppbase/src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: { rejectUnauthorized: false },
});

const associateTag = process.env.AMAZON_ASSOCIATE_TAG || 'suppbase-22';

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'wpi').toLowerCase();
    const limit = Number(sp.get('limit') ?? 10);

    const sql = `
      select
        category_rank as rank,
        asin,
        title,
        brand,
        price,
        review_count,
        image_url,
        suppbase_score,
        monthly_sold,
        sales_rank_drops30,
        sales_rank_drops90,
        sales_rank_drops180,
        protein_type
      from v_ranking_japan
      where protein_type = $1
      order by category_rank asc
      limit $2
    `;

    const { rows } = await pool.query(sql, [type, limit]);

    return NextResponse.json({
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: null,
        reviewCount: r.review_count ?? 0,
        score: r.suppbase_score,
        imageUrl: r.image_url ?? null,
        monthlySold: r.monthly_sold ?? 0,
        salesRankDrops30: r.sales_rank_drops30 ?? 0,
        salesRankDrops90: r.sales_rank_drops90 ?? 0,
        salesRankDrops180: r.sales_rank_drops180 ?? 0,
        proteinType: r.protein_type ?? null,
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}?tag=${associateTag}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('[JP ranking error]', msg);

    return NextResponse.json(
      { items: [], errorHint: msg },
      { status: 500 }
    );
  }
}