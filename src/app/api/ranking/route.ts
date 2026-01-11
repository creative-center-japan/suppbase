// healthy-site/src/app/api/ranking/route.ts

export const runtime = 'nodejs';

import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL!,
  ssl: {
    rejectUnauthorized: false,
  },
});

export async function GET() {
  try {
    const result = await pool.query('SELECT 1 AS ok');
    return NextResponse.json({
      connected: true,
      result: result.rows,
    });
  } catch (e) {
    return NextResponse.json(
      {
        connected: false,
        error: String(e),
      },
      { status: 500 }
    );
  }
}
