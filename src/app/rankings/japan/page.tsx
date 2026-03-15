// src\app\rankings\japan\page.tsx

'use client';

import Link from 'next/link';

const genres = [
  {
    href: '/rankings/japan/protein',
    label: 'プロテインランキング',
    description: '直近30日の動きや月間販売数の目安をもとに比較',
  },
  {
    href: '/rankings/japan/supplements',
    label: 'サプリメントランキング',
    description: 'BCAA・EAAなどを最近の動きベースで整理',
  },
];

export default function JapanRankingOverview() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-14">
      <h1 className="text-4xl font-extrabold text-center mb-4 text-gray-900">
        ジャンル別ランキング
      </h1>

      <p className="text-center text-gray-500 mb-12 leading-relaxed">
        Keepaの公開データをもとに、
        直近30日のランキング変動回数や月間販売数の目安から
        日本向け商品を整理したランキングです。
      </p>

      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-8">
        {genres.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="
                group block h-full
                border-2 border-gray-200
                rounded-2xl p-8
                transition
                hover:border-green-600
                hover:shadow-lg
              "
            >
              <div
                className="text-2xl font-bold text-gray-900 mb-2
                              group-hover:text-green-700 transition"
              >
                {item.label}
              </div>

              <p className="text-sm text-gray-500 leading-relaxed">
                {item.description}
              </p>

              <div
                className="mt-6 inline-block
                              text-green-700 font-semibold
                              group-hover:text-green-800"
              >
                ランキングを見る →
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}