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
  dropRate: number | null;
  dropRateDiff: number | null;
  score: number | null;
  affiliateUrl: string;
};

// ★ loading を optional に変更
const RankingSection = (
  { items, loading }: { items: ProductItem[]; loading?: boolean }
) => {
  if (loading) {
    return <p className="text-center text-gray-400">ランキング読み込み中...</p>;
  }
  if (!items.length) {
    return <p className="text-center text-gray-400">データがありません</p>;
  }

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
            unoptimized={Boolean(item.imageUrl?.includes('amazon'))}
          />

          <div className="flex-1">
            {/* タイトル・ブランド */}
            <h3
              className={`text-lg font-semibold ${
                item.rank === 1
                  ? 'text-yellow-500 text-xl font-bold'
                  : item.rank === 2
                  ? 'text-gray-500'
                  : item.rank === 3
                  ? 'text-orange-500'
                  : ''
              }`}
            >
              #{item.rank} {item.title}
            </h3>
            <p className="text-sm text-gray-600">{item.brand}</p>

            {/* 数値 + Amazonボタン */}
            <div className="mt-4 flex items-end justify-between gap-4">
              <div className="text-sm text-gray-700 space-y-1">
                <p>価格: {item.price != null ? `${item.price.toLocaleString()}円` : '―'}</p>
                <p>
                  ドロップ回数: {item.dropRate ?? '―'}
                  {typeof item.dropRateDiff === 'number' &&
                    (item.dropRateDiff > 0
                      ? ` ↑${item.dropRateDiff}`
                      : item.dropRateDiff < 0
                      ? ` ↓${Math.abs(item.dropRateDiff)}`
                      : '')}
                </p>
                <p>スコア: {item.score != null && item.score > 0 ? item.score : '―'}</p>
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

export default function ProteinRankingPage() {
  const [activeTab, setActiveTab] = useState<'whey' | 'soy' | 'isolate'>('whey');
  const [wheyItems, setWheyItems] = useState<ProductItem[]>([]);
  const [soyItems, setSoyItems] = useState<ProductItem[]>([]);
  const [isolateItems, setIsolateItems] = useState<ProductItem[]>([]);
  const [titleMonth, setTitleMonth] = useState<string>('');

  useEffect(() => {
    const fmt = new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: 'long',
      timeZone: 'Asia/Tokyo',
    });
    setTitleMonth(fmt.format(new Date()));
  }, []);

  useEffect(() => {
    fetch('/api/ranking?type=whey&sort=score', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => setWheyItems(data || []));
    fetch('/api/ranking?type=soy&sort=score', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => setSoyItems(data || []));
    fetch('/api/ranking?type=isolate&sort=score', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => setIsolateItems(data || []));
  }, []);

  const items =
    activeTab === 'soy'
      ? soyItems
      : activeTab === 'isolate'
      ? isolateItems
      : wheyItems;

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-1 text-center">
        {titleMonth ? `${titleMonth} プロテイン ランキング` : 'プロテイン ランキング'}
      </h1>
      <p className="text-sm text-gray-500 text-center mb-6">
        <Link href="/about#score" className="underline hover:text-green-700">
          SuppBaseスコアとは？
        </Link>
      </p>

      <div className="flex justify-center mb-6 gap-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'whey' | 'soy' | 'isolate')}
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

      {/* loading は渡さなくてOK */}
      <RankingSection items={items} />
    </main>
  );
}
