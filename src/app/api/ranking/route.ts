// healthy-site/src/app/api/ranking/route.ts

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
    const limit = Number(sp.get('limit') ?? 10);

    // ★ とにかく title ベースで出す
    let where = '';

    if (type === 'whey') {
      where = `WHERE title ILIKE '%ホエイ%' OR title ILIKE '%WHEY%'`;
    } else if (type === 'soy') {
      where = `WHERE title ILIKE '%ソイ%' OR title ILIKE '%SOY%'`;
    } else if (type === 'isolate') {
      where = `WHERE title ILIKE '%WPI%' OR title ILIKE '%アイソレート%'`;
    } else if (type === 'bcaa') {
      where = `WHERE title ILIKE '%BCAA%'`;
    }

    const sql = `
      SELECT
        asin,
        title,
        brand,
        imageurl,
        buyboxprice,
        rating,
        reviewcount,
        salesrank
      FROM products
      ${where}
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    return NextResponse.json(
      rows.map((p, i) => ({
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price: p.buyboxprice,
        rating: p.rating,
        reviewCount: p.reviewcount,
        imageUrl: p.imageurl,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      }))
    );
  } catch (e) {
    console.error('❌ ranking api error', e);
    return NextResponse.json([]);
  }
}
