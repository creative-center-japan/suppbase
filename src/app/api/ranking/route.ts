// healthy-site/src/app/api/ranking/route.ts

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
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = Number(sp.get('limit') ?? 20);

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

    // NOTE:
    // - products: imageUrl（キャメル）を想定
    // - product_snapshots: buyBoxPrice / reviewCount（キャメル）を想定
    // - もし snake_case の列なら COALESCE 側で拾う（ただし列自体が存在しないとSQLは失敗します）
    const sql = `
      SELECT
        p.asin,
        p.title,
        p.brand,
        p."imageUrl" AS image_url,
        COALESCE(s."buyBoxPrice", s.buybox_price) AS buybox_price,
        COALESCE(s.rating, s."rating") AS rating,
        COALESCE(s."reviewCount", s.review_count) AS review_count
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
      ORDER BY captured_at DESC NULLS LAST
      LIMIT $1
    `;

    const { rows } = await pool.query(sql, [limit]);

    const description =
      type === 'isolate'
        ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、公開データ（価格の動き・売れ筋指標・レビュー情報など）をもとに整理しています。実際の購入数を示すものではありません。'
        : type === 'soy'
        ? 'ソイプロテイン商品を対象に、公開データ（価格の動き・売れ筋指標・レビュー情報など）をもとに整理しています。売上数そのものを表すものではありません。'
        : type === 'supplement'
        ? 'サプリメント商品を対象に、公開データ（価格の動き・売れ筋指標・レビュー情報など）をもとに整理しています。売上順や効果を保証するものではありません。'
        : 'ホエイプロテイン商品のうちWPIを除いた商品を対象に、公開データをもとに整理しています。';

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
        imageUrl: p.image_url ?? null,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    // DBのパスワード等は出さない。SQL/カラム不一致のヒントだけ。
    return NextResponse.json({
      description: 'ランキング情報の取得に失敗しました。時間をおいて再度お試しください。',
      items: [],
      errorHint: msg,
    });
  }
}
