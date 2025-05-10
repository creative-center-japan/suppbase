import { NextRequest, NextResponse } from 'next/server';

export async function GET(_req: NextRequest) {
  return NextResponse.json(
    { error: 'Slug required in dynamic route.' },
    { status: 400 }
  );
}
