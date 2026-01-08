//healthy-site\src\app\rankings\japan\protein\page.tsx

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const tabs = [
  { id: 'whey', label: 'ホエイ' },
  { id: 'soy', label: 'ソイ' },
  { id: 'isolate', label: 'アイソレート（WPI）' },
];

type ProductItem = {
  rank: number;
  title: string;
  asin: string;
  brand: string;
  price: number | null;
  imageUrl: string;
  score: number | null;
  affiliateUrl: string;
};

export default function ProteinRankingPage() {
  const [activeTab, setActiveTab] =
    useState<'whey' | 'soy' | 'isolate'>('whey');
  const [wheyItems, setWheyItems] = useState<ProductItem[]>([]);
  const [soyItems, setSoyItems] = useState<ProductItem[]>([]);
  const [isolateItems, setIsolateItems] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    Promise.all([
      fetch(
        new URL('/api/ranking?type=whey&sort=score', window.location.origin),
        { cache: 'no-store' }
      ).then(r => r.json()),
      fetch(
        new URL('/api/ranking?type=soy&sort=score', window.location.origin),
        { cache: 'no-store' }
      ).then(r => r.json()),
      fetch(
        new URL('/api/ranking?type=isolate&sort=score', window.location.origin),
        { cache: 'no-store' }
      ).then(r => r.json()),
    ])
      .then(([whey, soy, isolate]) => {
        setWheyItems(Array.isArray(whey) ? whey : []);
        setSoyItems(Array.isArray(soy) ? soy : []);
        setIsolateItems(Array.isArray(isolate) ? isolate : []);
      })
      .finally(() => setLoading(false));
  }, []);

  const items =
    activeTab === 'soy'
      ? soyItems
      : activeTab === 'isolate'
      ? isolateItems
      : wheyItems;

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-center">
        プロテイン ランキング
      </h1>

      <div className="flex justify-center mb-6 gap-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() =>
              setActiveTab(tab.id as 'whey' | 'soy' | 'isolate')
            }
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

      {loading && <p className="text-center">読み込み中…</p>}
      {!loading && items.length === 0 && (
        <p className="text-center">データがありません</p>
      )}

      <div className="space-y-4">
        {items.map(item => (
          <div key={item.asin} className="p-4 border rounded-lg flex gap-4">
            <Image
              src={item.imageUrl || '/no-image.png'}
              alt={item.title}
              width={96}
              height={96}
              unoptimized
            />
            <div>
              <h3 className="font-semibold">
                #{item.rank} {item.title}
              </h3>
              <p className="text-sm text-gray-600">{item.brand}</p>
              <p>価格: {item.price ? `${item.price}円` : '―'}</p>
              <p>スコア: {item.score ?? '―'}</p>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
