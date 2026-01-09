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
    const limit = Number(sp.get('limit') ?? 20);

    /**
     * type → DB category 変換
     * - whey / soy / supplement がDBの正規カテゴリ
     * - isolate(WPI) は whey の派生表示
     * - bcaa は supplement に寄せる
     */
    const category =
      type === 'isolate' ? 'whey' :
      type === 'bcaa' ? 'supplement' :
      type;

    /**
     * isolate の場合のみ追加条件
     */
    const isolateWhere =
      type === 'isolate'
        ? `AND (title ILIKE '%isolate%' OR title ILIKE '%アイソレート%' OR title ILIKE '%WPI%')`
        : '';

    const sql = `
      SELECT
        asin,
        title,
        brand,
        buyboxprice,
        rating,
        reviewcount,
        score
      FROM v_rank_products_30d
      WHERE category = $1
      ${isolateWhere}
      ORDER BY score DESC
      LIMIT $2
    `;

    const { rows } = await pool.query(sql, [category, limit]);

    return NextResponse.json(
      rows.map((p, i) => ({
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price: p.buyboxprice,
        rating: p.rating,
        reviewCount: p.reviewcount,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      }))
    );
  } catch (e) {
    console.error('❌ ranking api error', e);
    return NextResponse.json([]);
  }
}
