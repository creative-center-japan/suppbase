// healthy-site\src\app\api\ranking\route.ts

export const runtime = 'nodejs';
import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// Vercelの関数で接続数が増えないよう、Poolをグローバル再利用
let _pool: Pool | null = null;
function getPool() {
  if (_pool) return _pool;
  _pool = new Pool({ connectionString: process.env.DATABASE_URL });
  return _pool;
}

// DB取得結果の型
type ProductRow = {
  asin: string;
  title: string;
  brand: string | null;
  buyboxprice: number | null;
  buyboxfallback: number | null;
  salesrank: number | null;
  droprate: number | null;
  droprateprev: number | null;
  imageurl: string | null;
};

export async function GET(req: NextRequest) {
  try {
    const searchParams = new URL(req.url).searchParams;
    const type = searchParams.get('type') ?? 'all';
    const sort = searchParams.get('sort') ?? 'drop';
    const limit = Number(searchParams.get('limit') ?? '10');

    // WHERE句
    let whereClause = '';
    if (type === 'whey') {
      whereClause = "WHERE title ILIKE '%ホエイ%' OR title ILIKE '%WPI%'";
    } else if (type === 'soy') {
      whereClause = "WHERE title ILIKE '%ソイ%'";
    } else if (type === 'isolate') {
      whereClause = "WHERE title ILIKE '%WPI%' OR title ILIKE '%アイソレート%'";
    } else if (type === 'bcaa') {
      whereClause = "WHERE title ILIKE '%BCAA%' OR title ILIKE '%bcaa%'";
    } else if (type === 'eaa') {
      whereClause = "WHERE title ILIKE '%EAA%' OR title ILIKE '%eaa%'";
    } else if (type === 'other') {
      whereClause = `
        WHERE title NOT ILIKE '%ホエイ%'
          AND title NOT ILIKE '%WPI%'
          AND title NOT ILIKE '%ソイ%'
          AND title NOT ILIKE '%アイソレート%'
          AND title NOT ILIKE '%BCAA%'
          AND title NOT ILIKE '%EAA%'
          AND title NOT ILIKE '%bcaa%'
          AND title NOT ILIKE '%eaa%'
      `;
    }

    // ORDER BY句（列名は小文字で統一）
    let orderClause = 'ORDER BY droprate DESC';
    if (sort === 'score') {
      orderClause = 'ORDER BY (COALESCE(droprate,0) * 2 + (10000 - COALESCE(salesrank, 10000))) DESC';
    } else if (sort === 'sales') {
      orderClause = 'ORDER BY salesrank ASC';
    } else if (sort === 'price') {
      orderClause = 'ORDER BY COALESCE(buyboxprice, buyboxfallback) ASC';
    }

    const sql = `
      SELECT asin, title, brand, buyboxprice, buyboxfallback, salesrank, droprate, droprateprev, imageurl
      FROM products
      ${whereClause}
      ${orderClause}
      LIMIT $1
    `;

    const pool = getPool();
    const { rows } = await pool.query<ProductRow>(sql, [limit]);

    const results = rows.map((item, index) => {
      const score = (item.droprate ?? 0) * 2 + (10000 - (item.salesrank ?? 10000));
      const rawPrice = item.buyboxprice ?? item.buyboxfallback;
      const price = rawPrice != null ? Math.round(rawPrice / 100) : null;
      const dropDiff = (item.droprate ?? 0) - (item.droprateprev ?? 0);
      return {
        rank: index + 1,
        asin: item.asin,
        title: item.title,
        brand: item.brand,
        price,
        dropRate: item.droprate,
        dropRateDiff: dropDiff,
        score,
        imageUrl: item.imageurl,
        affiliateUrl: `https://www.amazon.co.jp/dp/${item.asin}?tag=yourtag-22`,
      };
    });

    return NextResponse.json(results);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error('❌ /api/ranking error:', message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
