export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

let _pool: Pool | null = null;

function normalizeDbUrl(raw: string) {
  const u = new URL(raw);
  if (!u.searchParams.has('sslmode')) u.searchParams.set('sslmode', 'require');
  if (!u.searchParams.has('target_session_attrs')) {
    u.searchParams.set('target_session_attrs', 'read-write');
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

/** imageurl 正規化（最終防波堤） */
function normalizeImageUrl(imageurl: string | null): string | null {
  if (!imageurl) return null;

  if (imageurl.startsWith('https://images-na.ssl-images-amazon.com/images/I/')) {
    return imageurl;
  }

  if (imageurl.startsWith('https://images-na.ssl-images-amazon.com')) {
    const filename = imageurl.replace(
      /^https:\/\/images-na\.ssl-images-amazon\.com\/?/,
      ''
    );
    return `https://images-na.ssl-images-amazon.com/images/I/${filename}`;
  }

  if (!imageurl.startsWith('http')) {
    return `https://images-na.ssl-images-amazon.com/images/I/${imageurl}`;
  }

  return null;
}

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = 10;

    let table = 'products';
    let where = '';

    if (type === 'whey') table = 'v_rank_whey_30d';
    else if (type === 'isolate') table = 'v_rank_wpi_30d';
    else if (type === 'soy') {
      where = `
        WHERE imageurl IS NOT NULL
          AND (title ILIKE '%ソイ%' OR title ILIKE '%soy%' OR title ILIKE '%SOY%')
      `;
    } else if (type === 'bcaa') {
      where = `
        WHERE imageurl IS NOT NULL
          AND (title ILIKE '%BCAA%' OR title ILIKE '%bcaa%' OR title ILIKE '%ＢＣＡＡ%')
      `;
    } else if (type === 'eaa') {
      where = `
        WHERE imageurl IS NOT NULL
          AND (title ILIKE '%EAA%' OR title ILIKE '%eaa%' OR title ILIKE '%ＥＡＡ%')
      `;
    }

    const order = `ORDER BY COALESCE(score, 0) DESC, updated_at DESC`;

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
      pickCol(cols, 'score', 'score'),
      pickCol(cols, 'imageurl', 'imageurl'),
    ].join(',\n');

    const sql = `
      SELECT ${selectParts}
      FROM ${table}
      ${where}
      ${order}
      LIMIT $1
    `;

    const { rows } = await pool.query<any>(sql, [limit]);

    return NextResponse.json(
      rows.map((p: any, i: number) => ({
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price: p.buyboxprice
          ? Math.round(p.buyboxprice / 100)
          : p.buyboxfallback
          ? Math.round(p.buyboxfallback / 100)
          : null,
        score: p.score ?? 0,
        imageUrl: normalizeImageUrl(p.imageurl),
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      }))
    );
  } catch (e) {
    console.error('❌ /api/ranking error:', e);
    return NextResponse.json([], { status: 200 });
  }
}
