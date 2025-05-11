'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const tabs = [
  { id: 'bcaa', label: 'BCAA' },
  { id: 'eaa', label: 'EAA' }
];

type ProductItem = {
  rank: number;
  title: string;
  asin: string;
  brand: string;
  price: number | null;
  imageUrl: string;
  dropRate: number;
  dropRateDiff: number;
  score: number;
  affiliateUrl: string;
};

const RankingSection = ({ items }: { items: ProductItem[] }) => {
  if (!items.length) return <p className="text-center text-gray-400">ランキング読み込み中...</p>;

  return (
    <div className="space-y-4">
      {items.map(item => (
        <div
          key={item.asin}
          className={`p-4 rounded-xl shadow-sm hover:shadow-md transition flex gap-4 ${
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
            unoptimized={item.imageUrl?.includes('amazon') || false}
          />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <h3
                  className={`text-lg font-semibold ${
                    item.rank === 1
                      ? 'text-yellow-500 text-xl font-bold'
                      : item.rank === 2
                      ? 'text-gray-500 text-lg font-semibold'
                      : item.rank === 3
                      ? 'text-orange-500 font-semibold'
                      : ''
                  }`}
                >
                  #{item.rank} {item.title}
                </h3>
                <p className="text-sm text-gray-600">{item.brand}</p>
              </div>
              <div>
                <a
                  href={item.affiliateUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block w-32 h-9 bg-green-600 text-white text-sm text-center leading-9 rounded hover:bg-green-700"
                >
                  Amazonで見る
                </a>
              </div>
            </div>
            <div className="mt-2 text-sm text-gray-700">
              <p>価格: {item.price ? `${item.price.toLocaleString()}円` : '―'}</p>
              <p>
                ドロップ回数: {item.dropRate}
                {typeof item.dropRateDiff === 'number' &&
                  (item.dropRateDiff > 0
                    ? ` ↑${item.dropRateDiff}`
                    : item.dropRateDiff < 0
                    ? ` ↓${Math.abs(item.dropRateDiff)}`
                    : '')}
              </p>
              <p>スコア: {typeof item.score === 'number' && item.score > 0 ? item.score : '―'}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default function SupplementRankingPage() {
  const [activeTab, setActiveTab] = useState('bcaa');
  const [bcaaItems, setBcaaItems] = useState<ProductItem[]>([]);
  const [eaaItems, setEaaItems] = useState<ProductItem[]>([]);

  useEffect(() => {
    fetch('/api/ranking?type=bcaa&sort=score')
      .then(res => res.json())
      .then(data => setBcaaItems(data));
    fetch('/api/ranking?type=eaa&sort=score')
      .then(res => res.json())
      .then(data => setEaaItems(data));
  }, []);

  const getItems = () => {
    if (activeTab === 'eaa') return eaaItems;
    return bcaaItems;
  };

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4 text-center">2025年5月 サプリメント ランキング</h1>
      <p className="text-sm text-gray-500 text-center mb-6">
        <Link href="/about#score" className="underline hover:text-green-700">
          SuppBaseスコアとは？
        </Link>
      </p>

      <div className="flex justify-center mb-6 gap-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-full border font-medium transition ${
              activeTab === tab.id
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <RankingSection items={getItems()} />
    </main>
  );
}
