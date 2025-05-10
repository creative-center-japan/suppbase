import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json(
    { error: 'Slug required in dynamic route.' },
    { status: 400 }
  );
}
