export const runtime = 'nodejs';
import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

let _pool: Pool | null = null;

function normalizeDbUrl(raw: string) {
  const u = new URL(raw);

  // sslmode=require を強制
  if (!u.searchParams.has('sslmode')) u.searchParams.set('sslmode', 'require');
  if (!u.searchParams.has('target_session_attrs')) {
    u.searchParams.set('target_session_attrs', 'read-write');
  }

  // <project>.pooler.supabase.com のように「地域なし」なら地域付きへ矯正
  // 例: aws-0-ap-southeast-1.pooler.supabase.com
  if (/^[a-z0-9-]+\.pooler\.supabase\.com$/i.test(u.host)) {
    u.host = 'aws-0-ap-southeast-1.pooler.supabase.com';
  }

  return u;
}

function getPool() {
  if (_pool) return _pool;

  const raw = process.env.DATABASE_URL!;
  const url = normalizeDbUrl(raw);

  // デバッグ: Vercel Functions のログで確認できる
  console.log('DB host in use =>', url.host);

  _pool = new Pool({
    connectionString: url.toString(),
    ssl: { rejectUnauthorized: false }, // サーバレスで安定
  });
  return _pool;
}

// 型は小文字エイリアスに合わせる
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
    const sp = new URL(req.url).searchParams;
    const type = sp.get('type') ?? 'all';
    const sort = sp.get('sort') ?? 'drop';
    const limit = Math.max(1, Math.min(100, Number(sp.get('limit') ?? '10')));

    let where = '';
    if (type === 'whey') where = "WHERE title ILIKE '%ホエイ%' OR title ILIKE '%WPI%'";
    else if (type === 'soy') where = "WHERE title ILIKE '%ソイ%'";
    else if (type === 'isolate') where = "WHERE title ILIKE '%WPI%' OR title ILIKE '%アイソレート%'";
    else if (type === 'bcaa') where = "WHERE title ILIKE '%BCAA%' OR title ILIKE '%bcaa%'";
    else if (type === 'eaa') where = "WHERE title ILIKE '%EAA%' OR title ILIKE '%eaa%'";
    else if (type === 'other') where = `
      WHERE title NOT ILIKE '%ホエイ%'
        AND title NOT ILIKE '%WPI%'
        AND title NOT ILIKE '%ソイ%'
        AND title NOT ILIKE '%アイソレート%'
        AND title NOT ILIKE '%BCAA%'
        AND title NOT ILIKE '%EAA%'
        AND title NOT ILIKE '%bcaa%'
        AND title NOT ILIKE '%eaa%'
    `;

    let order = 'ORDER BY droprate DESC';
    if (sort === 'score') {
      order = 'ORDER BY (COALESCE(droprate,0)*2 + (10000-COALESCE(salesrank,10000))) DESC';
    } else if (sort === 'sales') {
      order = 'ORDER BY salesrank ASC NULLS LAST';
    } else if (sort === 'price') {
      order = 'ORDER BY COALESCE(buyboxprice, buyboxfallback) ASC NULLS LAST';
    }

    // 大文字混じりも拾えるよう AS で小文字エイリアス
    const sql = `
      SELECT
        asin,
        title,
        brand,
        COALESCE("buyboxprice","buyBoxPrice")             AS buyboxprice,
        COALESCE("buyboxfallback","buyBoxFallback")       AS buyboxfallback,
        COALESCE("salesrank","salesRank")                 AS salesrank,
        COALESCE("droprate","dropRate")                   AS droprate,
        COALESCE("droprateprev","dropRatePrev")           AS droprateprev,
        COALESCE("imageurl","imageUrl")                   AS imageurl
      FROM products
      ${where}
      ${order}
      LIMIT $1
    `;

    const pool = getPool();
    const { rows } = await pool.query<ProductRow>(sql, [limit]);

    const results = rows.map((item, i) => {
      const score = (item.droprate ?? 0) * 2 + (10000 - (item.salesrank ?? 10000));
      const rawPrice = item.buyboxprice ?? item.buyboxfallback;
      const price = rawPrice != null ? Math.round(rawPrice / 100) : null;
      const diff = (item.droprate ?? 0) - (item.droprateprev ?? 0);

      return {
        rank: i + 1,
        asin: item.asin,
        title: item.title,
        brand: item.brand,
        price,
        dropRate: item.droprate,
        dropRateDiff: diff,
        score,
        imageUrl: item.imageurl,
        affiliateUrl: `https://www.amazon.co.jp/dp/${item.asin}?tag=yourtag-22`,
      };
    });

    return NextResponse.json(results);
  } catch (e: any) {
    console.error('❌ /api/ranking error:', e?.message || e);
    return NextResponse.json({ error: String(e?.message || e) }, { status: 500 });
  }
}
