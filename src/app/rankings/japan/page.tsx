'use client';

import Link from 'next/link';

const genres = [
  { href: '/rankings/japan/protein', label: 'プロテインランキング', icon: '🧬' },
  { href: '/rankings/japan/foods', label: 'フードランキング', icon: '🍱' },
  { href: '/rankings/japan/supplements', label: 'サプリメントランキング', icon: '💊' },
  { href: '/rankings/japan/others', label: 'その他ランキング', icon: '🧩' },
];

export default function JapanRankingOverview() {
  return (
    <main className="max-w-xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-center mb-8">ジャンル別ランキング</h1>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {genres.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="flex items-center justify-start gap-4 p-6 h-24 border rounded-lg hover:bg-gray-50 text-lg font-medium text-green-700 shadow-sm transition"
            >
              <span className="text-3xl">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
