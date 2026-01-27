// src/app/api/ranking/route.ts

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
    const limit = Number(sp.get('limit') ?? 10);

    const sql = `
      SELECT
        rank,
        asin,
        title,
        brand,
        price,
        review_count,
        image_url,
        suppbase_score
      FROM v_ranking_latest_new
      ORDER BY rank
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    return NextResponse.json({
      description:
        '公開データをもとに、価格の安定性・需要の継続性などを考慮してスコア化しています。',
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: null, // ← 今回は未使用（将来追加OK）
        reviewCount: r.review_count,
        score: r.suppbase_score,
        imageUrl: r.image_url ?? null,
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('[API ranking error]', msg);
    return NextResponse.json(
      {
        description:
          'ランキング情報の取得に失敗しました。時間をおいて再度お試しください。',
        items: [],
        errorHint: msg,
      },
      { status: 500 }
    );
  }
}
