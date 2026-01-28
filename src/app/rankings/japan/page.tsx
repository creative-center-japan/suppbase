// src\app\rankings\japan\page.tsx

'use client';

import Link from 'next/link';

const genres = [
  {
    href: '/rankings/japan/protein',
    label: 'プロテインランキング',
    description: 'WPI・ソイなど、目的別に比較',
  },
  {
    href: '/rankings/japan/supplements',
    label: 'サプリメントランキング',
    description: 'BCAA・EAAなど運動向けサプリ',
  },
];

export default function JapanRankingOverview() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-14">
      {/* タイトル */}
      <h1 className="text-4xl font-extrabold text-center mb-4 text-gray-900">
        ジャンル別ランキング
      </h1>

      <p className="text-center text-gray-500 mb-12">
        SuppBase 独自スコアによる、日本向け商品ランキング
      </p>

      {/* カード */}
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
              {/* ラベル */}
              <div className="text-2xl font-bold text-gray-900 mb-2
                              group-hover:text-green-700 transition">
                {item.label}
              </div>

              {/* 説明 */}
              <p className="text-sm text-gray-500 leading-relaxed">
                {item.description}
              </p>

              {/* 擬似ボタン */}
              <div className="mt-6 inline-block
                              text-green-700 font-semibold
                              group-hover:text-green-800">
                ランキングを見る →
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
