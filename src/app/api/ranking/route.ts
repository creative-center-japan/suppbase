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
};

let _pool: Pool | null = null;

function normalizeDbUrl(raw: string) {
  const u = new URL(raw);
  if (!u.searchParams.has('sslmode')) {
    u.searchParams.set('sslmode', 'require');
  }
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

// ===== imageurl 正規化（最終防波堤）=====
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
    const sort = (sp.get('sort') ?? 'score').toLowerCase();
    const limit = 10;

    /**
     * ★ ここが今回の本丸 ★
     * ランキングの参照先を v_suppbase_score_phase1 に統一
     */
    let table = 'v_suppbase_score_phase1';
    let where = '';

    // type ごとの差分は WHERE で吸収
    if (type === 'soy') {
      where = `
        WHERE (
          title ILIKE '%ソイ%' OR
          title ILIKE '%soy%' OR
          title ILIKE '%SOY%' OR
          title ILIKE '%大豆%' OR
          title ILIKE '%植物性%'
        )
      `;
    } else if (type === 'isolate') {
      where = `
        WHERE (
          title ILIKE '%WPI%' OR
          title ILIKE '%アイソレート%'
        )
      `;
    } else {
      // whey（デフォルト）
      where = '';
    }

    // ===== ORDER =====
    let order = `
      ORDER BY
        COALESCE(score, 0) DESC,
        COALESCE(droprate, 0) DESC,
        calculated_at DESC
    `;

    if (sort === 'price') {
      order = `
        ORDER BY
          COALESCE(buyboxprice, buyboxfallback) ASC NULLS LAST,
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

    // ===== カラム存在チェック =====
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
      pickCol(cols, 'droprate', 'droprate'),
      pickCol(cols, 'droprateprev', 'droprateprev'),
      pickCol(cols, 'score', 'score'),
      pickCol(cols, 'imageurl', 'imageurl'),
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
        dropRate: p.droprate ?? 0,
        dropRateDiff: (p.droprate ?? 0) - (p.droprateprev ?? 0),
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
