import fs from "fs";
import path from "path";
import matter from "gray-matter";
import Markdown from "react-markdown";

interface ArticlePageProps {
  params: {
    slug: string;
  };
}

export default function ArticlePage({ params }: ArticlePageProps) {
  const filePath = path.join(process.cwd(), "articles", `${params.slug}.md`);
  const fileContent = fs.readFileSync(filePath, "utf-8");
  const { data, content } = matter(fileContent);

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <article className="prose prose-lg max-w-none">
        <h1 className="text-3xl font-bold mb-4">{data.title}</h1>
        <p className="text-sm text-gray-500 mb-6">{new Date(data.date).toLocaleDateString()}</p>
        <Markdown>{content}</Markdown>
      </article>
    </main>
  );
}
