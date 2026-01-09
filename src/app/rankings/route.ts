// healthy-site\src\app\rankings\route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

type Row = {
  rank: number;
  asin: string;
  title: string;
  brand: string | null;
  imageurl: string | null;
  buyboxprice: number | null;
  salesrank: number | null;
  rating: number | null;
  reviewcount: number | null;
  score: number | null;
};

let _pool: Pool | null = null;

function getPool() {
  if (_pool) return _pool;
  _pool = new Pool({
    connectionString: process.env.DATABASE_URL!,
    ssl: { rejectUnauthorized: false },
  });
  return _pool;
}

function normalizeImageUrl(imageurl: string | null): string | null {
  if (!imageurl) return null;
  if (imageurl.startsWith('http')) return imageurl;
  return `https://images-na.ssl-images-amazon.com/images/I/${imageurl}`;
}

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;
    const type = (sp.get('type') ?? 'whey').toLowerCase();
    const limit = 10;

    let where = '';

    // ★ title ベース分類（category は使わない）
    if (type === 'whey') {
      where = `
        WHERE title NOT ILIKE '%WPI%'
          AND title NOT ILIKE '%アイソレート%'
          AND title NOT ILIKE '%ソイ%'
          AND title NOT ILIKE '%soy%'
      `;
    } else if (type === 'isolate') {
      where = `
        WHERE title ILIKE '%WPI%'
           OR title ILIKE '%アイソレート%'
      `;
    } else if (type === 'soy') {
      where = `
        WHERE title ILIKE '%ソイ%'
           OR title ILIKE '%soy%'
      `;
    }

    const sql = `
      SELECT
        ROW_NUMBER() OVER (
          ORDER BY COALESCE(score,0) DESC
        ) AS rank,
        asin,
        title,
        brand,
        imageurl,
        buyboxprice,
        salesrank,
        rating,
        reviewcount,
        score
      FROM v_suppbase_score_phase1
      ${where}
      ORDER BY rank
      LIMIT $1
    `;

    const pool = getPool();
    const { rows } = await pool.query<Row>(sql, [limit]);

    const items = rows.map(p => {
      const price =
        p.buyboxprice != null
          ? p.buyboxprice > 1000
            ? Math.round(p.buyboxprice / 100)
            : p.buyboxprice
          : null;

      return {
        rank: p.rank,
        asin: p.asin,
        title: p.title,
        brand: p.brand ?? '',
        price,
        score: p.score,
        rating: p.rating,
        reviewCount: p.reviewcount,
        imageUrl: normalizeImageUrl(p.imageurl),
        affiliateUrl: `https://www.amazon.co.jp/dp/${p.asin}`,
      };
    });

    return NextResponse.json(items);
  } catch (e) {
    console.error('❌ /api/ranking error:', e);
    return NextResponse.json([], { status: 200 });
  }
}
