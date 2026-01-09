// healthy-site\src\app\api\ranking\route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

type Row = {
  asin: string;
  title: string;
  brand: string | null;
  imageurl: string | null;
  buyboxprice: number | null;
  salesrank: number | null;
  rating: number | null;
  reviewcount: number | null;
  score: number | null;
  display_category: string | null;
};

let _pool: Pool | null = null;

function getPool() {
  if (_pool) return _pool;
  _pool = new Pool({
    connectionString: process.env.DATABASE_URL!,
    ssl: { rejectUnauthorized: false },
  });
  return _pool;
}

function normalizeImageUrl(imageurl: string | null): string | null {
  if (!imageurl) return null;
  if (imageurl.startsWith('http')) return imageurl;
  return `https://images-na.ssl-images-amazon.com/images/I/${imageurl}`;
}

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = 10;

    let where = '';

    if (type === 'whey') {
      where = `WHERE t.display_category = 'whey'`;
    } else if (type === 'soy') {
      where = `WHERE t.display_category = 'soy'`;
    } else if (type === 'isolate') {
      where = `WHERE t.display_category = 'isolate'`;
    } else if (type === 'bcaa') {
      where = `WHERE t.display_category IN ('bcaa','supplement')`;
    } else {
      // フォールバック（安全）
      where = `WHERE t.display_category IS NOT NULL`;
    }

    const sql = `
      SELECT
        v.asin,
        v.title,
        v.brand,
        v.imageurl,
        v.buyboxprice,
        v.salesrank,
        v.rating,
        v.reviewcount,
        v.score,
        t.display_category
      FROM v_suppbase_score_phase1 v
      JOIN tracked_asins t ON t.asin = v.asin
      ${where}
      ORDER BY COALESCE(v.score, 0) DESC
      LIMIT $1
    `;

    const pool = getPool();
    const { rows } = await pool.query<Row>(sql, [limit]);

    const items = rows.map((p, i) => ({
      rank: i + 1,
      asin: p.asin,
      title: p.title,
      brand: p.brand ?? '',
      price:
        p.buyboxprice != null
          ? p.buyboxprice > 1000
            ? Math.round(p.buyboxprice / 100)
            : p.buyboxprice
          : null,
      score: p.score ?? 0,
      rating: p.rating,
      reviewCount: p.reviewcount,
      imageUrl: normalizeImageUrl(p.imageurl),
      affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
    }));

    return NextResponse.json(items);
  } catch (e) {
    console.error('❌ /api/ranking error:', e);
    return NextResponse.json([], { status: 200 });
  }
}
