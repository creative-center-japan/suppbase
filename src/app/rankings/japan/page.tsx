// src\app\rankings\japan\page.tsx

'use client';

import Link from 'next/link';

const genres = [
  { href: '/rankings/japan/protein', label: 'プロテインランキング' },
  { href: '/rankings/japan/supplements', label: 'サプリメントランキング' },
];

export default function JapanRankingOverview() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-center mb-8">
        ジャンル別ランキング
      </h1>

      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {genres.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="block border rounded-lg p-6 text-center hover:bg-gray-50 transition"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
