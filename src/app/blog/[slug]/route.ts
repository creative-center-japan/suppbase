import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import matter from 'gray-matter';

export async function GET(
  req: NextRequest,
  context: { params?: Record<string, string | string[]> }
) {
  try {
    const slug = context.params?.slug;
    if (typeof slug !== 'string') {
      return NextResponse.json({ error: 'Invalid slug' }, { status: 400 });
    }

    const filePath = path.join(process.cwd(), 'articles', `${slug}.md`);
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }

    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const { data, content } = matter(fileContent);

    return NextResponse.json({ title: data.title, date: data.date, content });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: 'Error reading article' }, { status: 500 });
  }
}
