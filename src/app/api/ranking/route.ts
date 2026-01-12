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
    const locale = (sp.get('locale') ?? 'jp').toLowerCase(); // ★追加
    const limit = Number(sp.get('limit') ?? 10);

    let whereClause = `
      p.locale = $2
      AND t.locale = $2
    `;

    if (type === 'isolate') {
      whereClause += ` AND p.protein_type = 'wpi'`;
    } else if (type === 'soy') {
      whereClause += ` AND t.category = 'soy'`;
    } else if (type === 'supplement') {
      whereClause += ` AND t.category = 'supplement'`;
    } else {
      whereClause += `
        AND t.category = 'whey'
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
      INNER JOIN tracked_asins t
        ON t.asin = p.asin
        AND t.locale = p.locale
      LEFT JOIN latest_product_scores sc
        ON sc.asin = p.asin
        AND sc.locale = p.locale
      LEFT JOIN LATERAL (
        SELECT *
        FROM product_snapshots
        WHERE asin = p.asin
          AND locale = p.locale
        ORDER BY captured_at DESC
        LIMIT 1
      ) s ON true
      WHERE ${whereClause}
      ORDER BY sc.score DESC NULLS LAST
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit, locale]);

    const description =
      type === 'isolate'
        ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、公開データ（売れ筋指標・価格変動・レビュー情報など）をもとにスコア化しています。'
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
        score: p.score,
        affiliateUrl:
          locale === 'us'
            ? `https://www.amazon.com/dp/${p.asin}`
            : `https://www.amazon.co.jp/dp/${p.asin}`,
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
