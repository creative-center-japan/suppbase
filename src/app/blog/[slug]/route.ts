// src/app/blog/[slug]/route.ts

import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import matter from 'gray-matter';

export async function GET(
  req: NextRequest,
  { params }: { params: { slug: string } }
) {
  try {
    const filePath = path.join(process.cwd(), 'articles', `${params.slug}.md`);

    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }

    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const { data, content } = matter(fileContent);

    return NextResponse.json({ title: data.title, date: data.date, content });
  } catch (err) {
    return NextResponse.json({ error: 'Error reading article' }, { status: 500 });
  }
}
