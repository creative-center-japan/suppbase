export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

let _pool: Pool | null = null;

function normalizeDbUrl(raw: string) {
  const u = new URL(raw);
  if (!u.searchParams.has('sslmode')) u.searchParams.set('sslmode', 'require');
  if (!u.searchParams.has('target_session_attrs')) u.searchParams.set('target_session_attrs', 'read-write');
  if (/^[a-z0-9-]+\.pooler\.supabase\.com$/i.test(u.host)) {
    u.host = 'aws-0-ap-southeast-1.pooler.supabase.com';
  }
  return u;
}
function getPool() {
  if (_pool) return _pool;
  const url = normalizeDbUrl(process.env.DATABASE_URL!);
  _pool = new Pool({ connectionString: url.toString(), ssl: { rejectUnauthorized: false } });
  return _pool;
}

function pickCol(cols: Set<string>, lower: string, camel: string, alias: string) {
  if (cols.has(lower)) return `"${lower}" AS ${alias}`;
  if (cols.has(camel)) return `"${camel}" AS ${alias}`;
  return `NULL AS ${alias}`;
}

type ProductRow = {
  asin: string;
  title: string;
  brand: string | null;
  buyboxprice: number | null;
  buyboxfallback: number | null;
  salesrank: number | null;
  droprate: number | null;
  droprateprev: number | null;
  imageurl: string | null;
  score: number | null;
};

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'bcaa').toLowerCase();
    const sort = sp.get('sort') ?? 'score';
    const limit = Math.max(1, Math.min(100, Number(sp.get('limit') ?? '50')));

    // === where 条件（全角/半角を両方サポート）===
    const where =
      type === 'eaa'
        ? `WHERE title ILIKE '%EAA%' OR title ILIKE '%eaa%' OR title ILIKE '%ＥＡＡ%'`
        : `WHERE title ILIKE '%BCAA%' OR title ILIKE '%bcaa%' OR title ILIKE '%ＢＣＡＡ%'`;

    let order = 'ORDER BY score DESC NULLS LAST';
    if (sort === 'droprate') order = 'ORDER BY droprate DESC NULLS LAST';
    else if (sort === 'sales') order = 'ORDER BY salesrank ASC NULLS LAST';
    else if (sort === 'price') order = 'ORDER BY COALESCE(buyboxprice, buyboxfallback) ASC NULLS LAST';

    const pool = getPool();

    const meta = await pool.query<{ column_name: string }>(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema='public' AND table_name='products'
    `);
    const cols = new Set(meta.rows.map(r => r.column_name));

    const selectParts = [
      pickCol(cols, 'asin', 'asin', 'asin'),
      pickCol(cols, 'title', 'title', 'title'),
      pickCol(cols, 'brand', 'brand', 'brand'),
      pickCol(cols, 'buyboxprice', 'buyBoxPrice', 'buyboxprice'),
      pickCol(cols, 'buyboxfallback', 'buyBoxFallback', 'buyboxfallback'),
      pickCol(cols, 'salesrank', 'salesRank', 'salesrank'),
      pickCol(cols, 'droprate', 'dropRate', 'droprate'),
      pickCol(cols, 'droprateprev', 'dropRatePrev', 'droprateprev'),
      pickCol(cols, 'imageurl', 'imageUrl', 'imageurl'),
      pickCol(cols, 'score', 'score', 'score'),
    ].join(',\n        ');

    const sql = `
      SELECT
        ${selectParts}
      FROM products
      ${where}
      ${order}
      LIMIT $1
    `;

    const { rows } = await pool.query<ProductRow>(sql, [limit]);

    const items = rows.map((p, i) => {
      const rawPrice = p.buyboxprice ?? p.buyboxfallback;
      const price = rawPrice != null ? Math.round(rawPrice / 100) : null;
      const diff = (p.droprate ?? 0) - (p.droprateprev ?? 0);

      return {
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price,
        imageUrl: p.imageurl,
        dropRate: p.droprate,
        dropRateDiff: diff,
        score: p.score ?? null,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      };
    });

    return NextResponse.json(items);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('❌ /api/supplements error:', msg);
    return NextResponse.json([], { status: 200 });
  }
}
