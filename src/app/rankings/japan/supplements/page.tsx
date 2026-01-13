// healthy-site\src\app\rankings\japan\supplements\page.tsx

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: { rejectUnauthorized: false },
});

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const limit = Number(sp.get('limit') ?? 10);

    const sql = `
      SELECT
        row_number() over (order by v.score desc nulls last) as rank,
        v.asin,
        v.title,
        v.brand,
        v.buybox_price as price,
        v.rating,
        v.review_count,
        v.score
      FROM v_product_score_latest v
      JOIN products p USING (asin)
      WHERE p.sub_category = 'supplement'
      ORDER BY v.score DESC NULLS LAST
      LIMIT $1
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
        rating: r.rating,
        reviewCount: r.review_count,
        score: r.score,
        imageUrl: `https://images-na.ssl-images-amazon.com/images/P/${r.asin}.01._SL300_.jpg`,
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({
      description: 'サプリメントランキングの取得に失敗しました。',
      items: [],
      errorHint: msg,
    });
  }
}
