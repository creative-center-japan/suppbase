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

    const type = (sp.get('type') ?? 'wpi').toLowerCase();
    const limit = Number(sp.get('limit') ?? 10);

    const sql = `
      SELECT
        rank,
        asin,
        title,
        brand,
        price,
        rating,
        review_count,
        score
      FROM v_ranking_latest
      WHERE protein_type = $1
      ORDER BY rank
      LIMIT $2
    `;

    const { rows } = await pool.query(sql, [type, limit]);

    return NextResponse.json({
      description:
        type === 'wpi'
          ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、公開データをもとにスコア化しています。'
          : 'プロテイン商品を対象に、公開データをもとにスコア化しています。',
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: r.rating,
        reviewCount: r.review_count,
        score: r.score,
        imageUrl: null, // ※ 今回は未使用（後で products JOIN してもOK）
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({
      description:
        'ランキング情報の取得に失敗しました。時間をおいて再度お試しください。',
      items: [],
      errorHint: msg,
    });
  }
}
