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
     * タブごとの抽出条件
     * - isolate(WPI): protein_type = 'wpi' のみ
     * - soy: category = 'soy'
     * - whey: category = 'whey' かつ WPI除外
     */
    let whereClause = '';

    if (type === 'isolate') {
      // WPIタブ
      whereClause = `p.protein_type = 'wpi'`;
    } else if (type === 'soy') {
      // ソイタブ
      whereClause = `t.category = 'soy'`;
    } else {
      // ホエイタブ（WPI除外）
      whereClause = `
        t.category = 'whey'
        AND p.protein_type != 'wpi'
      `;
    }

    /**
     * ランキング取得SQL
     * - 最新の snapshot を1件だけ取得
     * - snapshot が無くても表示されるよう LEFT JOIN
     */
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
      JOIN tracked_asins t ON t.asin = p.asin
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

    return NextResponse.json(
      rows.map((p, i) => ({
        rank: i + 1,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price: p.buybox_price,
        rating: p.rating,
        reviewCount: p.review_count,
        imageUrl: p.image_url,
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      }))
    );
  } catch (e) {
    console.error('❌ ranking api error', e);
    return NextResponse.json([]);
  }
}
