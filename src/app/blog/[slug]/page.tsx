// healthy-site\src\app\blog\[slug]\page.tsx

export const dynamic = "force-static";

import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { notFound } from "next/navigation";
import Link from "next/link";

type Props = { params: { slug: string } };

const articlesDir = path.join(process.cwd(), "articles");

export function generateStaticParams() {
  const files = fs.existsSync(articlesDir) ? fs.readdirSync(articlesDir) : [];
  return files
    .filter((f) => f.endsWith(".md"))
    .map((f) => ({ slug: f.replace(/\.md$/, "") }));
}

export default function ArticlePage({ params }: Props) {
  const slug = params?.slug;
  if (!slug) notFound();

  const filePath = path.join(articlesDir, `${slug}.md`);
  if (!fs.existsSync(filePath)) notFound();

  const raw = fs.readFileSync(filePath, "utf-8");
  const { data, content } = matter(raw);

  return (
    <main className="max-w-3xl mx-auto px-4 py-12 prose">
      <Link href="/blog" className="no-underline text-green-700">
        ← Back to Blog
      </Link>
      <h1 className="mt-2">{data.title}</h1>
      <p className="text-sm text-gray-500">
        {data.date ? new Date(data.date).toLocaleDateString() : ""}
      </p>
      {/* とりあえず生描画。あとで remark に置き換え可 */}
      <article className="mt-6 whitespace-pre-wrap">{content}</article>
    </main>
  );
}
