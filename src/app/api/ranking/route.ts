// healthy-site/src/app/api/ranking/route.ts

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
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = Number(sp.get('limit') ?? 20);

    /**
     * 表示タイプ → DB条件
     */
    let categoryWhere = '';
    let proteinTypeWhere = '';

    if (type === 'isolate') {
      categoryWhere = `t.category = 'whey'`;
      proteinTypeWhere = `AND p.protein_type = 'wpi'`;
    } else if (type === 'soy') {
      categoryWhere = `t.category = 'soy'`;
    } else {
      // whey（WPI除外）
      categoryWhere = `t.category = 'whey'`;
      proteinTypeWhere = `AND (p.protein_type IS NULL OR p.protein_type != 'wpi')`;
    }

    /**
     * 最新 snapshot を使う
     */
    const sql = `
      SELECT
        p.asin,
        p.title,
        p.brand,
        p.image_url,
        s.buybox_price,
        s.rating,
        s.review_count
      FROM products p
      JOIN tracked_asins t ON t.asin = p.asin
      JOIN LATERAL (
        SELECT *
        FROM product_snapshots
        WHERE asin = p.asin
        ORDER BY captured_at DESC
        LIMIT 1
      ) s ON true
      WHERE ${categoryWhere}
      ${proteinTypeWhere}
      ORDER BY s.buybox_price ASC NULLS LAST
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    return NextResponse.json(
      rows.map((p, i) => ({
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price: p.buybox_price,
        rating: p.rating,
        reviewCount: p.review_count,
        imageUrl: p.image_url,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      }))
    );
  } catch (e) {
    console.error('❌ ranking api error', e);
    return NextResponse.json([]);
  }
}
