// healthy-site/src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: { rejectUnauthorized: false },
});

type Row = {
  asin: string;
  title: string;
  brand: string | null;
  imageurl: string | null;
  buyboxprice: number | null;
  rating: number | null;
  reviewcount: number | null;
  salesrank: number | null;
  score: number | null;
};

function normalizeImageUrl(imageurl: string | null): string | null {
  if (!imageurl) return null;
  if (imageurl.startsWith('http')) return imageurl;
  return `https://images-na.ssl-images-amazon.com/images/I/${imageurl}`;
}

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;

    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const sort = (sp.get('sort') ?? 'score').toLowerCase();
    const limit = Number(sp.get('limit') ?? 10);

    // ★ VIEW 切替（これが全て）
    let viewName = 'v_rank_whey_30d';

    if (type === 'soy') viewName = 'v_rank_soy_30d';
    if (type === 'isolate') viewName = 'v_rank_wpi_30d';

    // 並び順（基本は score）
    let orderBy = 'score DESC';

    if (sort === 'price') orderBy = 'buyboxprice ASC NULLS LAST';
    if (sort === 'sales') orderBy = 'salesrank ASC NULLS LAST';

    const sql = `
      SELECT
        asin,
        title,
        brand,
        imageurl,
        buyboxprice,
        rating,
        reviewcount,
        salesrank,
        score
      FROM ${viewName}
      ORDER BY ${orderBy}
      LIMIT $1
    `;

    const { rows } = await pool.query<Row>(sql, [limit]);

    const items = rows.map((p, i) => ({
      rank: i + 1,
      asin: p.asin,
      title: p.title,
      brand: p.brand ?? '',
      price:
        p.buyboxprice != null
          ? p.buyboxprice > 1000
            ? Math.round(p.buyboxprice / 100)
            : p.buyboxprice
          : null,
      score: p.score ?? 0,
      rating: p.rating,
      reviewCount: p.reviewcount,
      imageUrl: normalizeImageUrl(p.imageurl),
      affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
    }));

    return NextResponse.json(items);
  } catch (e) {
    console.error('❌ /api/ranking error:', e);
    return NextResponse.json([], { status: 200 });
  }
}