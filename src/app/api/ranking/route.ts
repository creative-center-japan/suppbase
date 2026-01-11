// healthy-site/src/app/api/ranking/route.ts

// src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: {
    rejectUnauthorized: false,
  },
});

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = Number(sp.get('limit') ?? 20);

    let whereClause = '';

    if (type === 'isolate') {
      // WPI
      whereClause = `p.protein_type = 'wpi'`;
    } else if (type === 'soy') {
      // ソイ
      whereClause = `t.category = 'soy'`;
    } else if (type === 'supplement') {
      // サプリメント
      whereClause = `t.category = 'supplement'`;
    } else {
      // ホエイ（WPI除外）
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
        p.image_url,
        s.buybox_price,
        s.rating,
        s.review_count
      FROM products p
      LEFT JOIN tracked_asins t ON t.asin = p.asin
      LEFT JOIN LATERAL (
        SELECT *
        FROM product_snapshots
        WHERE asin = p.asin
        ORDER BY captured_at DESC
        LIMIT 1
      ) s ON true
      WHERE ${whereClause}
      ORDER BY s.captured_at DESC NULLS LAST
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    const description =
      type === 'isolate'
        ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、価格の動きや売れ筋指標などの公開情報をもとに、最近の注目度が高そうな商品を整理しています。実際の購入数を示すものではありません。'
        : type === 'soy'
        ? 'ソイプロテイン商品を対象に、価格の変化や売れ筋指標などの公開データをもとに整理しています。販売数そのものを表すものではなく、動きのある商品を見つけるための参考情報です。'
        : type === 'supplement'
        ? 'サプリメント商品を対象に、価格の変化や売れ筋指標などの公開情報をもとに整理しています。売上順や効果を保証するものではありません。'
        : 'ホエイプロテイン商品のうちWPIを除いた商品を対象に、公開されている指標をもとに整理しています。';

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
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      })),
    });
  } catch (e) {
    console.error('ranking api error', e);
    return NextResponse.json({
      description:
        'ランキング情報の取得に失敗しました。時間をおいて再度お試しください。',
      items: [],
    });
  }
}
