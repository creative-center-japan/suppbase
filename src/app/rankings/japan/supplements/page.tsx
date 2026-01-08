// healthy-site\src\app\rankings\japan\supplements\page.tsx

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

type ProductItem = {
  rank: number;
  title: string;
  asin: string;
  brand: string;
  price: number | null;
  imageUrl: string | null;
  score: number | null;
  affiliateUrl: string;
};

const RankingSection = ({
  items,
  loading,
}: {
  items: ProductItem[];
  loading?: boolean;
}) => {
  if (loading) {
    return (
      <p className="text-center text-gray-400 py-8">
        ランキング読み込み中…
      </p>
    );
  }

  if (!items.length) {
    return (
      <p className="text-center text-gray-400 py-8">
        データがありません
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <div
          key={item.asin}
          className={`p-4 rounded-xl shadow-sm hover:shadow-md transition flex gap-4 ${
            index === 0
              ? 'border-2 border-yellow-400'
              : index === 1
              ? 'border-2 border-gray-400'
              : index === 2
              ? 'border-2 border-orange-400'
              : 'border border-gray-200'
          }`}
        >
          <Image
            src={
              item.imageUrl && item.imageUrl.startsWith('http')
                ? item.imageUrl
                : '/no-image.png'
            }
            alt={item.title}
            width={96}
            height={96}
            className="object-contain rounded"
            unoptimized
          />

          <div className="flex-1">
            <h3
              className={`text-lg font-semibold ${
                index === 0
                  ? 'text-yellow-500 text-xl font-bold'
                  : index === 1
                  ? 'text-gray-500'
                  : index === 2
                  ? 'text-orange-500'
                  : ''
              }`}
            >
              #{index + 1} {item.title}
            </h3>

            <p className="text-sm text-gray-600">{item.brand}</p>

            <div className="mt-4 flex items-end justify-between gap-4">
              <div className="text-sm text-gray-700 space-y-1">
                <p>
                  価格:{' '}
                  {item.price != null
                    ? `${item.price.toLocaleString()}円`
                    : '―'}
                </p>
                <p>
                  スコア:{' '}
                  {item.score != null && item.score > 0 ? item.score : '―'}
                </p>
              </div>

              <a
                href={item.affiliateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 inline-flex items-center justify-center
                           rounded-md bg-green-600 px-4 py-2
                           text-white text-sm font-semibold
                           hover:bg-green-700 transition"
              >
                Amazonで見る
              </a>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default function SupplementRankingPage() {
  const [items, setItems] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [titleMonth, setTitleMonth] = useState('');

  useEffect(() => {
    const fmt = new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: 'long',
      timeZone: 'Asia/Tokyo',
    });
    setTitleMonth(fmt.format(new Date()));
  }, []);

  useEffect(() => {
    setLoading(true);

    // ★ basePath 環境対応：必ず origin 付きで叩く
    fetch(
      new URL('/api/ranking?type=bcaa&sort=score', window.location.origin),
      { cache: 'no-store' }
    )
      .then(res => res.json())
      .then(data => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-1 text-center">
        {titleMonth
          ? `${titleMonth} サプリメント ランキング`
          : 'サプリメント ランキング'}
      </h1>

      <p className="text-sm text-gray-500 text-center mb-6">
        <Link href="/about#score" className="underline hover:text-green-700">
          SuppBaseスコアとは？
        </Link>
      </p>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
