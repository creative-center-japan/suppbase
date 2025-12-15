// healthy-site/src/app/api/supplements/route.ts

export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
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

// 実在カラムだけ SELECT
function pickCol(cols: Set<string>, lower: string, alias: string) {
  if (cols.has(lower)) return `"${lower}" AS ${alias}`;
  return `NULL AS ${alias}`;
}

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

export async function GET() {
  try {
    // ★ 常に TOP10 固定
    const limit = 10;

    // ★ BCAA + EAA をまとめたサプリランキング
    //   プロテイン系は除外
    const where = `
      WHERE (
        title ILIKE '%BCAA%' OR title ILIKE '%bcaa%' OR title ILIKE '%ＢＣＡＡ%' OR
        title ILIKE '%EAA%'  OR title ILIKE '%eaa%'  OR title ILIKE '%ＥＡＡ%'
      )
      AND title NOT ILIKE '%プロテイン%'
      AND title NOT ILIKE '%protein%'
      AND title NOT ILIKE '%ホエイ%'
      AND title NOT ILIKE '%whey%'
      AND title NOT ILIKE '%wpc%'
      AND title NOT ILIKE '%wpi%'
    `;

    // ★ スコア未成熟でも順位が安定する並び
    const order = `
      ORDER BY
        COALESCE(score, 0) DESC,
        COALESCE(droprate, 0) DESC,
        updated_at DESC
    `;

    const pool = getPool();

    // 実在カラム取得
    const meta = await pool.query<{ column_name: string }>(`
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema='public'
        AND table_name='products'
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
      FROM products
      ${where}
      ${order}
      LIMIT $1
    `;

    const { rows } = await pool.query<Row>(sql, [limit]);

    // ★ rank は UI 用に 1〜10 で再採番
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
        imageUrl: p.imageurl,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      };
    });

    return NextResponse.json(items);
  } catch (e) {
    console.error('❌ /api/supplements error:', e);
    // フロントを壊さないため 200 + 空配列
    return NextResponse.json([], { status: 200 });
  }
}
