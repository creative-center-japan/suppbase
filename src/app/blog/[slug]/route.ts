import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import matter from 'gray-matter';

export async function GET(
  req: NextRequest,
  context: { params: { slug: string } }
) {
  try {
    const { slug } = context.params;
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
