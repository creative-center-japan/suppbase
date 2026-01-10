// healthy-site/src/app/api/ranking/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

export const runtime = 'nodejs';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: { rejectUnauthorized: false },
});

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = Number(sp.get('limit') ?? 20);

    let whereClause = '';

    if (type === 'isolate') {
      whereClause = `p.protein_type = 'wpi'`;
    } else if (type === 'soy') {
      whereClause = `t.category = 'soy'`;
    } else {
      whereClause = `
        t.category = 'whey'
        AND p.protein_type != 'wpi'
      `;
    }

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
      LEFT JOIN tracked_asins t ON t.asin = p.asin
      LEFT JOIN LATERAL (
        SELECT *
        FROM product_snapshots
        WHERE asin = p.asin
        ORDER BY captured_at DESC
        LIMIT 1
      ) s ON true
      WHERE ${whereClause}
      ORDER BY s.captured_at DESC NULLS LAST
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    return NextResponse.json(rows);
  } catch (e) {
    console.error('ranking api error', e);
    return NextResponse.json([]);
  }
}
