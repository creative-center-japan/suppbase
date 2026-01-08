// healthy-site/src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

type Row = {
  asin: string;
  title: string;
  brand: string | null;
  buyboxprice: number | null; // ★ 円
  salesrank: number | null;
  score: number | null;
  imageurl: string | null;
  category: string | null;
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
    const sort = (sp.get('sort') ?? 'score').toLowerCase();
    const limit = 10;

    const table = 'v_suppbase_score_phase1';
    let where = '';

    // ★ category 実値に合わせて柔軟に
    if (type === 'whey') {
      where = `WHERE category ILIKE '%whey%'`;
    } else if (type === 'soy') {
      where = `WHERE category ILIKE '%soy%'`;
    } else if (type === 'isolate') {
      where = `WHERE category ILIKE '%wpi%' OR category ILIKE '%isolate%'`;
    } else if (type === 'bcaa') {
      where = `WHERE category ILIKE '%bcaa%'`;
    }

    let order = `
      ORDER BY
        COALESCE(score,0) DESC,
        calculated_at DESC
    `;

    if (sort === 'price') {
      order = `
        ORDER BY
          buyboxprice ASC NULLS LAST,
          calculated_at DESC
      `;
    } else if (sort === 'sales') {
      order = `
        ORDER BY
          salesrank ASC NULLS LAST,
          calculated_at DESC
      `;
    }

    const pool = getPool();
    const sql = `
      SELECT
        asin,
        title,
        brand,
        imageurl,
        buyboxprice,
        salesrank,
        score,
        category
      FROM ${table}
      ${where}
      ${order}
      LIMIT $1
    `;

    const { rows } = await pool.query<Row>(sql, [limit]);

    const items = rows.map((p, i) => ({
      rank: i + 1,
      asin: p.asin,
      title: p.title,
      brand: p.brand ?? '',
      price: p.buyboxprice,            // ★ ÷100しない
      score: p.score ?? 0,
      imageUrl: normalizeImageUrl(p.imageurl),
      affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
    }));

    return NextResponse.json(items);
  } catch (e) {
    console.error('❌ /api/ranking error:', e);
    return NextResponse.json([], { status: 200 });
  }
}
