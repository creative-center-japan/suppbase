'use client';

import Link from 'next/link';

const genres = [
  { href: '/rankings/japan/protein', label: 'プロテインランキング' },
  { href: '/rankings/japan/foods', label: 'フードランキング' },
  { href: '/rankings/japan/supplements', label: 'サプリメントランキング' },
  { href: '/rankings/japan/others', label: 'その他ランキング' },
];

export default function JapanRankingOverview() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-center mb-8">ジャンル別ランキング</h1>

      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {genres.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="flex items-center justify-center p-8 h-28 rounded-2xl
                         border border-gray-100 bg-gradient-to-br from-white to-gray-50
                         text-lg font-semibold text-gray-800 shadow-md
                         hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
