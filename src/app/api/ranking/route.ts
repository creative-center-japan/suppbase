// healthy-site/src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

type Row = {
  asin: string;
  title: string;
  brand: string | null;
  buyboxprice: number | null;
  buyboxfallback: number | null;
  salesrank: number | null;
  droprate: number | null;
  droprateprev: number | null;
  score: number | null;
  imageurl: string | null;
  category: string | null;
};

let _pool: Pool | null = null;

function normalizeDbUrl(raw: string) {
  const u = new URL(raw);
  if (!u.searchParams.has('sslmode')) {
    u.searchParams.set('sslmode', 'require');
  }
  return u;
}

function getPool() {
  if (_pool) return _pool;
  const url = normalizeDbUrl(process.env.DATABASE_URL!);
  _pool = new Pool({
    connectionString: url.toString(),
    ssl: { rejectUnauthorized: false },
  });
  return _pool;
}

function pickCol(cols: Set<string>, lower: string, alias: string) {
  return cols.has(lower) ? `"${lower}" AS ${alias}` : `NULL AS ${alias}`;
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

    if (type === 'whey') where = `WHERE category = 'whey'`;
    else if (type === 'soy') where = `WHERE category = 'soy'`;
    else if (type === 'isolate')
      where = `WHERE category IN ('wpi','isolate')`;

    let order = `
      ORDER BY
        COALESCE(score,0) DESC,
        calculated_at DESC
    `;

    if (sort === 'price') {
      order = `
        ORDER BY
          COALESCE(buyboxprice,buyboxfallback) ASC NULLS LAST,
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

    const meta = await pool.query<{ column_name: string }>(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema='public'
        AND table_name='${table}'
    `);

    const cols = new Set(meta.rows.map(r => r.column_name));

    const selectParts = [
      pickCol(cols, 'asin', 'asin'),
      pickCol(cols, 'title', 'title'),
      pickCol(cols, 'brand', 'brand'),
      pickCol(cols, 'buyboxprice', 'buyboxprice'),
      pickCol(cols, 'buyboxfallback', 'buyboxfallback'),
      pickCol(cols, 'salesrank', 'salesrank'),
      pickCol(cols, 'score', 'score'),
      pickCol(cols, 'imageurl', 'imageurl'),
      pickCol(cols, 'category', 'category'),
    ].join(',\n');

    const sql = `
      SELECT
        ${selectParts}
      FROM ${table}
      ${where}
      ${order}
      LIMIT $1
    `;

    const { rows } = await pool.query<Row>(sql, [limit]);

    const items = rows.map((p, i) => {
      const rawPrice = p.buyboxprice ?? p.buyboxfallback;
      const price = rawPrice != null ? Math.round(rawPrice / 100) : null;

      return {
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price,
        score: p.score ?? 0,
        imageUrl: normalizeImageUrl(p.imageurl),
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      };
    });

    return NextResponse.json(items);
  } catch (e) {
    console.error('❌ /api/ranking error:', e);
    return NextResponse.json([], { status: 200 });
  }
}
