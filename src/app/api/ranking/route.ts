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

    // ★ タブから来る type
    const type = (sp.get('type') ?? 'wpi').toLowerCase();
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
      FROM v_ranking_japan
      WHERE protein_type = $1
      ORDER BY rank
      LIMIT $2
    `;

    const { rows } = await pool.query(sql, [type, limit]);

    return NextResponse.json({
      description:
        type === 'wpi'
          ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、公開データをもとにスコア化しています。'
          : 'ソイプロテインとして分類された商品の中から、公開データをもとにスコア化しています。',
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: null,
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
      { items: [], errorHint: msg },
      { status: 500 }
    );
  }
}
