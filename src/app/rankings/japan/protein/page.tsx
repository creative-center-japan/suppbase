//healthy-site\src\app\rankings\japan\protein\page.tsx

'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';

const tabs = [
  { id: 'whey', label: 'ホエイ' },
  { id: 'soy', label: 'ソイ' },
  { id: 'isolate', label: 'アイソレート（WPI）' },
];

type ProductItem = {
  rank: number;
  asin: string;
  title: string;
  brand: string;
  price: number | null;
  imageUrl: string | null;
  score: number | null;
  affiliateUrl: string;
};

export default function ProteinRankingPage() {
  const [activeTab, setActiveTab] =
    useState<'whey' | 'soy' | 'isolate'>('whey');
  const [items, setItems] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(
      new URL(`/api/ranking?type=${activeTab}&sort=score`, window.location.origin),
      { cache: 'no-store' }
    )
      .then(r => r.json())
      .then(data => setItems(Array.isArray(data) ? data : []))
      .finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-center">
        プロテイン ランキング
      </h1>

      <div className="flex justify-center mb-6 gap-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-full border ${
              activeTab === tab.id
                ? 'bg-green-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-center text-gray-400">読み込み中…</p>}
      {!loading && items.length === 0 && (
        <p className="text-center text-gray-400">データがありません</p>
      )}

      <div className="space-y-4">
        {items.map(item => (
          <div
            key={item.asin}
            className={`p-4 rounded-xl shadow-sm flex gap-4 ${
              item.rank === 1
                ? 'border-2 border-yellow-400'
                : item.rank === 2
                ? 'border-2 border-gray-400'
                : item.rank === 3
                ? 'border-2 border-orange-400'
                : 'border border-gray-200'
            }`}
          >
            <Image
              src={item.imageUrl || '/no-image.png'}
              alt={item.title}
              width={96}
              height={96}
              className="object-contain rounded"
              unoptimized
            />

            <div className="flex-1">
              <h3 className="font-semibold">
                #{item.rank} {item.title}
              </h3>
              <p className="text-sm text-gray-600">{item.brand}</p>
              <p className="mt-2">
                価格:{' '}
                {item.price != null
                  ? `${item.price.toLocaleString()}円`
                  : '―'}
              </p>
              <p>スコア: {item.score ?? '―'}</p>

              <a
                href={item.affiliateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-2 text-sm text-green-700 underline"
              >
                Amazonで見る
              </a>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
