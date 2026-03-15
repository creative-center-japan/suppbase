// uppbase\src\app\api\ranking\japan\supplement\route.ts

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
        sales_rank_drops180
      from v_ranking_japan_bcaa_eaa
      order by category_rank
      limit $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    return NextResponse.json({
      description:
        'BCAA / EAA サプリメントを対象に、直近30日のランキング変動回数と月間販売数の目安をもとに整理しています。',
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: null,
        reviewCount: r.review_count,
        score: r.suppbase_score,
        imageUrl: r.image_url ?? null,
        monthlySold: r.monthly_sold ?? 0,
        salesRankDrops30: r.sales_rank_drops30 ?? 0,
        salesRankDrops90: r.sales_rank_drops90 ?? 0,
        salesRankDrops180: r.sales_rank_drops180 ?? 0,
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}?tag=${associateTag}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('[JP supplement ranking error]', msg);

    return NextResponse.json(
      { items: [], errorHint: msg },
      { status: 500 }
    );
  }
}