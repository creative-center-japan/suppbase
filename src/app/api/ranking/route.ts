import { NextRequest, NextResponse } from 'next/server';
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.resolve(process.cwd(), 'public', 'mydata.db'); // ← 修正箇所

export async function GET(req: NextRequest) {
  try {
    const db = new Database(DB_PATH);

    const { searchParams } = new URL(req.url);
    const type = searchParams.get('type') ?? 'all';
    const sort = searchParams.get('sort') ?? 'drop';
    const limit = parseInt(searchParams.get('limit') ?? '10');

    let whereClause = '';
    if (type === 'whey') {
      whereClause = "WHERE title LIKE '%ホエイ%' OR title LIKE '%WPI%'";
    } else if (type === 'soy') {
      whereClause = "WHERE title LIKE '%ソイ%'";
    } else if (type === 'isolate') {
      whereClause = "WHERE title LIKE '%WPI%' OR title LIKE '%アイソレート%'";
    } else if (type === 'bcaa') {
      whereClause = "WHERE title LIKE '%BCAA%' OR title LIKE '%bcaa%'";
    } else if (type === 'eaa') {
      whereClause = "WHERE title LIKE '%EAA%' OR title LIKE '%eaa%'";
    } else if (type === 'other') {
      whereClause = `
        WHERE title NOT LIKE '%ホエイ%'
        AND title NOT LIKE '%WPI%'
        AND title NOT LIKE '%ソイ%'
        AND title NOT LIKE '%アイソレート%'
        AND title NOT LIKE '%BCAA%'
        AND title NOT LIKE '%EAA%'
        AND title NOT LIKE '%bcaa%'
        AND title NOT LIKE '%eaa%'
      `;
    }

    let orderClause = 'ORDER BY dropRate DESC';
    if (sort === 'score') {
      orderClause = 'ORDER BY (dropRate * 2 + (10000 - COALESCE(salesRank, 10000))) DESC';
    } else if (sort === 'sales') {
      orderClause = 'ORDER BY salesRank ASC';
    } else if (sort === 'price') {
      orderClause = 'ORDER BY COALESCE(buyBoxPrice, buyBoxFallback) ASC';
    }

    type ProductRow = {
      asin: string;
      title: string;
      brand: string;
      buyBoxPrice: number | null;
      buyBoxFallback: number | null;
      salesRank: number | null;
      dropRate: number;
      dropRatePrev: number;
      imageUrl: string;
    };

    const stmt = db.prepare(`
      SELECT asin, title, brand, buyBoxPrice, buyBoxFallback, salesRank, dropRate, dropRatePrev, imageUrl
      FROM products
      ${whereClause}
      ${orderClause}
      LIMIT ?
    `);

    const results = (stmt.all(limit) as ProductRow[]).map((item, index) => {
      const score = item.dropRate * 2 + (10000 - (item.salesRank ?? 10000));
      const rawPrice = item.buyBoxPrice ?? item.buyBoxFallback;
      const price = rawPrice ? Math.round(rawPrice / 100) : null;
      const dropDiff = item.dropRate - (item.dropRatePrev ?? 0);

      return {
        rank: index + 1,
        asin: item.asin,
        title: item.title,
        brand: item.brand,
        price,
        dropRate: item.dropRate,
        dropRateDiff: dropDiff,
        score,
        imageUrl: item.imageUrl,
        affiliateUrl: `https://www.amazon.co.jp/dp/${item.asin}?tag=yourtag-22`
      };
    });

    return NextResponse.json(results);

  } catch (err) {
    console.error("❌ API error:", err);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
