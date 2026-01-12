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
    const limit = Number(sp.get('limit') ?? 10);

    let whereClause = '';

    if (type === 'isolate') {
      whereClause = `p.protein_type = 'wpi'`;
    } else if (type === 'soy') {
      whereClause = `t.category = 'soy'`;
    } else if (type === 'supplement') {
      whereClause = `t.category = 'supplement'`;
    } else {
      whereClause = `
        t.category = 'whey'
        AND p.protein_type != 'wpi'
      `;
    }

    const sql = `
      SELECT
        p.asin,
        p.title,
        p.brand,
        p."imageUrl"          AS image_url,
        s.buybox_price       AS buybox_price,
        s.rating             AS rating,
        s.review_count       AS review_count,
        sc.score             AS score
      FROM products p
      LEFT JOIN tracked_asins t
        ON t.asin = p.asin
      LEFT JOIN latest_product_scores sc
        ON sc.asin = p.asin
      LEFT JOIN LATERAL (
        SELECT *
        FROM product_snapshots
        WHERE asin = p.asin
        ORDER BY captured_at DESC
        LIMIT 1
      ) s ON true
      WHERE ${whereClause}
      ORDER BY sc.score DESC NULLS LAST
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    const description =
      type === 'isolate'
        ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、公開データ（価格の動き・売れ筋指標・レビュー情報など）をもとにスコア化しています。'
        : type === 'soy'
        ? 'ソイプロテイン商品を対象に、公開データをもとにスコア化しています。'
        : type === 'supplement'
        ? 'サプリメント商品を対象に、公開データをもとにスコア化しています。'
        : 'ホエイプロテイン商品のうちWPIを除いた商品を対象に、公開データをもとにスコア化しています。';

    return NextResponse.json({
      description,
      items: rows.map((p, i) => ({
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price: p.buybox_price,
        rating: p.rating,
        reviewCount: p.review_count,
        imageUrl: p.image_url,
        score: p.score, // ← ここが新規
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
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
