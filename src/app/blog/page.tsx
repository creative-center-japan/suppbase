export const dynamic = "force-static"; // ← 追加これだけ！

import fs from "fs";
import path from "path";
import matter from "gray-matter";
import Link from "next/link";

interface ArticleMeta {
  slug: string;
  title: string;
  date: string;
  summary: string;
}

export default function BlogListPage() {
  const articlesDir = path.join(process.cwd(), "articles");
  const files = fs.readdirSync(articlesDir);

  const articles: ArticleMeta[] = files.map((file) => {
    const filePath = path.join(articlesDir, file);
    const content = fs.readFileSync(filePath, "utf-8");
    const { data } = matter(content);

    return {
      slug: file.replace(".md", ""),
      title: data.title,
      date: data.date,
      summary: data.summary,
    };
  });

  articles.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-6">Blog</h1>
      <div className="grid gap-6 sm:grid-cols-2">
        {articles.map((article) => (
          <div key={article.slug} className="bg-white shadow p-6 rounded-lg border border-gray-100">
            <h2 className="text-xl font-semibold text-green-700">
              <Link href={`/blog/${article.slug}`} className="hover:underline">
                {article.title}
              </Link>
            </h2>
            <p className="text-sm text-gray-500">{new Date(article.date).toLocaleDateString()}</p>
            <p className="text-gray-700 mt-2">{article.summary}</p>
            <Link
              href={`/blog/${article.slug}`}
              className="text-sm text-green-600 hover:underline mt-4 inline-block"
            >
              Read more →
            </Link>
          </div>
        ))}
      </div>
    </main>
  );
}
