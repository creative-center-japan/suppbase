import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// 環境変数 DATABASE_URL を使用
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

// DB取得結果の型を明確に定義
type ProductRow = {
  asin: string;
  title: string;
  brand: string;
  buyboxprice: number | null;
  buyboxfallback: number | null;
  salesrank: number | null;
  droprate: number;
  droprateprev: number | null;
  imageurl: string;
};

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const type = searchParams.get('type') ?? 'all';
    const sort = searchParams.get('sort') ?? 'drop';
    const limit = parseInt(searchParams.get('limit') ?? '10');

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

    // ORDER BY句
    let orderClause = 'ORDER BY dropRate DESC';
    if (sort === 'score') {
      orderClause = 'ORDER BY (dropRate * 2 + (10000 - COALESCE(salesRank, 10000))) DESC';
    } else if (sort === 'sales') {
      orderClause = 'ORDER BY salesRank ASC';
    } else if (sort === 'price') {
      orderClause = 'ORDER BY COALESCE(buyBoxPrice, buyBoxFallback) ASC';
    }

    // SQLクエリ作成
    const query = `
      SELECT asin, title, brand, buyBoxPrice, buyBoxFallback, salesRank, dropRate, dropRatePrev, imageUrl
      FROM products
      ${whereClause}
      ${orderClause}
      LIMIT $1
    `;
    const { rows } = await pool.query<ProductRow>(query, [limit]);

    // 整形（型指定済）
    const results = rows.map((item: ProductRow, index: number) => {
      const score = item.droprate * 2 + (10000 - (item.salesrank ?? 10000));
      const rawPrice = item.buyboxprice ?? item.buyboxfallback;
      const price = rawPrice ? Math.round(rawPrice / 100) : null;
      const dropDiff = item.droprate - (item.droprateprev ?? 0);

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
    console.error('❌ API error:', err);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
