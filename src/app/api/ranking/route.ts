// healthy-site/src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

let _pool: Pool | null = null;

function normalizeDbUrl(raw: string) {
  const u = new URL(raw);
  if (!u.searchParams.has('sslmode')) {
    u.searchParams.set('sslmode', 'require');
  }
  if (!u.searchParams.has('target_session_attrs')) {
    u.searchParams.set('target_session_attrs', 'read-write');
  }
  // ★ host の書き換えは絶対にしない
  return u;
}

function getPool() {
  if (_pool) return _pool;

  const url = normalizeDbUrl(process.env.DATABASE_URL!);
  console.log('DB host in use =>', url.host);

  _pool = new Pool({
    connectionString: url.toString(),
    ssl: { rejectUnauthorized: false },
  });

  return _pool;
}

// 実在するカラムだけ SELECT に含める
function pickCol(cols: Set<string>, lower: string, alias: string) {
  if (cols.has(lower)) return `"${lower}" AS ${alias}`;
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
};

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = sp.get('type') ?? 'whey';
    const sort = sp.get('sort') ?? 'drop';
    const limit = Math.max(1, Math.min(100, Number(sp.get('limit') ?? '10')));

    // ✅ type ごとに参照 VIEW を切り替える
    let table = 'v_rank_wpi_30d';
    if (type === 'whey') table = 'v_rank_whey_30d';
    else if (type === 'soy') table = 'v_rank_soy_30d';
    else if (type === 'isolate') table = 'v_rank_wpi_30d';

    let order = 'ORDER BY droprate DESC';
    if (sort === 'score') {
      order =
        'ORDER BY (COALESCE(droprate,0)*2 + (10000-COALESCE(salesrank,10000))) DESC';
    } else if (sort === 'sales') {
      order = 'ORDER BY salesrank ASC NULLS LAST';
    } else if (sort === 'price') {
      order =
        'ORDER BY COALESCE(buyboxprice, buyboxfallback) ASC NULLS LAST';
    }

    const pool = getPool();

    // ✅ 選択した VIEW の実在カラムを取得
    const meta = await pool.query<{ column_name: string }>(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = '${table}'
    `);

    const cols = new Set(meta.rows.map((r) => r.column_name));
    console.log('Detected columns:', table, [...cols]);

    const selectParts = [
      pickCol(cols, 'asin', 'asin'),
      pickCol(cols, 'title', 'title'),
      pickCol(cols, 'brand', 'brand'),
      pickCol(cols, 'buyboxprice', 'buyboxprice'),
      pickCol(cols, 'buyboxfallback', 'buyboxfallback'),
      pickCol(cols, 'salesrank', 'salesrank'),
      pickCol(cols, 'droprate', 'droprate'),
      pickCol(cols, 'droprateprev', 'droprateprev'),
      pickCol(cols, 'imageurl', 'imageurl'),
    ].join(',\n        ');

    const sql = `
      SELECT
        ${selectParts}
      FROM ${table}
      ${order}
      LIMIT $1
    `;

    const { rows } = await pool.query<ProductRow>(sql, [limit]);

    const results = rows.map((item, i) => {
      const score =
        (item.droprate ?? 0) * 2 +
        (10000 - (item.salesrank ?? 10000));

      const rawPrice = item.buyboxprice ?? item.buyboxfallback;
      const price =
        rawPrice != null ? Math.round(rawPrice / 100) : null;

      const diff =
        (item.droprate ?? 0) - (item.droprateprev ?? 0);

      return {
        rank: i + 1,
        asin: item.asin,
        title: item.title,
        brand: item.brand,
        price,
        dropRate: item.droprate,
        dropRateDiff: diff,
        score,
        imageUrl: item.imageurl,
        affiliateUrl: `https://www.amazon.co.jp/dp/${item.asin}?tag=yourtag-22`,
      };
    });

    return NextResponse.json(results);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('/api/ranking error:', msg);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
