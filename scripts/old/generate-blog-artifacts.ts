// scripts/generate-blog-artifacts.ts
import fs from "fs";
import path from "path";
import matter from "gray-matter";

type Row = {
  slug: string;
  title: string;
  date?: string;
  summary?: string;
  file: string;
  url: string;
  warnings: string[];
};

const ROOT = process.cwd();
const ARTICLES_DIR = path.join(ROOT, "articles");
const PUBLIC_DIR = path.join(ROOT, "public");
const BASE_URL = process.env.SITE_URL?.replace(/\/+$/, "") || "https://example.com";

function assertDirs() {
  if (!fs.existsSync(ARTICLES_DIR)) {
    console.error(`❌ articles ディレクトリが見つかりません: ${ARTICLES_DIR}`);
    process.exit(1);
  }
  if (!fs.existsSync(PUBLIC_DIR)) fs.mkdirSync(PUBLIC_DIR);
}

function collect(): Row[] {
  const files = fs
    .readdirSync(ARTICLES_DIR)
    .filter((f) => f.endsWith(".md"))
    .sort();

  const rows: Row[] = [];

  for (const file of files) {
    const full = path.join(ARTICLES_DIR, file);
    const raw = fs.readFileSync(full, "utf-8");
    const { data, content } = matter(raw);

    const slug = file.replace(/\.md$/, "");
    const url = `${BASE_URL}/blog/${slug}`;
    const warnings: string[] = [];

    if (!data?.title) warnings.push("title がありません");
    if (!data?.date) warnings.push("date がありません");
    else if (isNaN(new Date(data.date).getTime())) warnings.push("date の形式が不正です");

    // フロントマター位置の簡易チェック
    if (!raw.trimStart().startsWith("---")) {
      warnings.push("frontmatter が先頭にありません（--- で囲って先頭に置いてください）");
    }
    // “記事本文がほぼない”などの軽いヒント
    if (content.trim().length < 50) warnings.push("本文が短すぎる可能性");

    rows.push({
      slug,
      title: data?.title ?? "(no title)",
      date: data?.date,
      summary: data?.summary,
      file,
      url,
      warnings,
    });
  }
  return rows;
}

function writeJson(rows: Row[]) {
  const jsonPath = path.join(PUBLIC_DIR, "blog-index.json");
  const payload = rows
    .slice()
    .sort((a, b) => {
      const ad = a.date ? new Date(a.date).getTime() : 0;
      const bd = b.date ? new Date(b.date).getTime() : 0;
      return bd - ad;
    })
    .map(({ slug, title, date, summary, url }) => ({ slug, title, date, summary, url }));

  fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2), "utf-8");
  console.log(`✅ public/blog-index.json を出力: ${payload.length} 件`);
}

function writeSitemap(rows: Row[]) {
  const urls = rows.map((r) => `  <url>\n    <loc>${r.url}</loc>\n  </url>`).join("\n");
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${BASE_URL}/</loc></url>
  <url><loc>${BASE_URL}/blog</loc></url>
${urls}
</urlset>`;
  const out = path.join(PUBLIC_DIR, "sitemap.xml");
  fs.writeFileSync(out, xml, "utf-8");
  console.log("✅ public/sitemap.xml を出力");
}

function printTable(rows: Row[]) {
  console.log("\n=== Blog URL 一覧 ===============================");
  for (const r of rows) {
    const warn = r.warnings.length ? ` ⚠ ${r.warnings.join(" / ")}` : "";
    console.log(`- /blog/${r.slug}  ← ${r.file}${warn}`);
  }
  console.log("===============================================\n");
}

(function main() {
  assertDirs();
  const rows = collect();
  printTable(rows);
  writeJson(rows);
  writeSitemap(rows);

  const hasWarn = rows.some((r) => r.warnings.length);
  if (hasWarn) {
    console.log("⚠ 一部記事で警告があります。上の一覧を確認してください。");
    process.exitCode = 0; // ビルドは止めない
  }
})();
