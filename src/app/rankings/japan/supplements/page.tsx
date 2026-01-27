// healthy-site\src\app\rankings\japan\supplements\page.tsx

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// PostgreSQL (Supabase) 接続
const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: { rejectUnauthorized: false },
});

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const limit = Number(sp.get('limit') ?? 10);

    const sql = `
      select
        category_rank as rank,     -- ★ サプリ内順位
        asin,
        title,
        brand,
        price,
        review_count,
        image_url,
        suppbase_score
      from v_ranking_japan
      where protein_type = 'supplement'
      order by category_rank
      limit $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    return NextResponse.json({
      description:
        'サプリメント商品を対象に、公開データをもとにスコア化しています。',
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: null, // 未使用
        reviewCount: r.review_count,
        score: r.suppbase_score,
        imageUrl: r.image_url ?? null,
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('[JP supplement ranking error]', msg);
    return NextResponse.json(
      {
        items: [],
        errorHint: msg,
      },
      { status: 500 }
    );
  }
}
