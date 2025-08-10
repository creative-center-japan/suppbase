// app/api/test-db/route.ts
import { NextResponse } from 'next/server'
import postgres from 'postgres'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  const url = process.env.DATABASE_URL!
  try {
    const sql = postgres(url, { ssl: 'require' }) // ← これでOK
    const rows = await sql`select * from products limit 5`
    await sql.end({ timeout: 1 })
    return NextResponse.json(rows)
  } catch (e:any) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
