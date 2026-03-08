// src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// PostgreSQL (Supabase) 接続
const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: { rejectUnauthorized: false },
});

const associateTag = process.env.AMAZON_ASSOCIATE_TAG || 'suppbase-22';

export async function GET(req: NextRequest) {
  try {
    const sp = new URL(req.url).searchParams;

    // タブから来る type（wpi / soy）
    const type = (sp.get('type') ?? 'wpi').toLowerCase();
    const limit = Number(sp.get('limit') ?? 10);

    // 想定外の type を弾く
    if (!['wpi', 'soy'].includes(type)) {
      return NextResponse.json(
        { items: [], errorHint: 'invalid protein type' },
        { status: 400 }
      );
    }

    const sql = `
      select
        category_rank as rank,
        asin,
        title,
        brand,
        price,
        review_count,
        image_url,
        suppbase_score
      from v_ranking_japan
      where protein_type = $1
      order by category_rank
      limit $2
    `;

    const { rows } = await pool.query(sql, [type, limit]);

    return NextResponse.json({
      description:
        type === 'wpi'
          ? 'WPI（ホエイプロテイン・アイソレート）として分類された商品の中から、公開データをもとにスコア化しています。'
          : 'ソイプロテインとして分類された商品の中から、公開データをもとにスコア化しています。',
      items: rows.map(r => ({
        rank: r.rank,
        asin: r.asin,
        title: r.title,
        brand: r.brand ?? '',
        price: r.price,
        rating: null,
        reviewCount: r.review_count,
        score: r.suppbase_score,
        imageUrl: r.image_url ?? null,
        affiliateUrl: `https://www.amazon.co.jp/dp/${r.asin}?tag=${associateTag}`,
      })),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error('[JP protein ranking error]', msg);

    return NextResponse.json(
      {
        items: [],
        errorHint: msg,
      },
      { status: 500 }
    );
  }
}