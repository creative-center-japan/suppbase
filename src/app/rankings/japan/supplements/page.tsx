// src/app/rankings/japan/supplements/page.tsx
'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const tabs = [
  { id: 'bcaa', label: 'BCAA' },
  { id: 'eaa',  label: 'EAA'  },
];

type ProductItem = {
  rank: number;
  title: string;
  asin: string;
  brand: string;
  price: number | null;
  imageUrl: string | null;
  dropRate: number | null;
  dropRateDiff: number | null;
  score: number | null;
  affiliateUrl: string;
  updatedAt?: string; // ★
};

function fmtRangeFromItems(items: ProductItem[], fallback = '直近30日') {
  if (!items?.length) return fallback;
  const ds = items
    .map(i => (i.updatedAt ? new Date(i.updatedAt) : null))
    .filter((d): d is Date => d instanceof Date && !isNaN(+d));
  if (!ds.length) return fallback;
  const min = new Date(Math.min(...ds.map(d => +d)));
  const max = new Date(Math.max(...ds.map(d => +d)));
  if (min.getUTCFullYear() === max.getUTCFullYear() && min.getUTCMonth() === max.getUTCMonth()) {
    return `${max.getUTCFullYear()}年${max.getUTCMonth() + 1}月`;
  }
  const md = (d: Date) => `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
  return `${md(min)}〜${md(max)}`;
}

const RankingSection = ({ items, loading }: { items: ProductItem[]; loading: boolean }) => {
  if (loading) return <p className="text-center text-gray-400">ランキング読み込み中...</p>;
  if (!items.length) return <p className="text-center text-gray-400">データがありません</p>;
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
            alt={item.title || 'supplement'}
            width={96}
            height={96}
            className="object-contain rounded"
            unoptimized={Boolean(item.imageUrl?.includes('amazon'))}
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
              <a
                href={item.affiliateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block w-32 h-9 bg-green-600 text-white text-sm text-center leading-9 rounded hover:bg-green-700"
              >
                Amazonで見る
              </a>
            </div>
            <div className="mt-2 text-sm text-gray-700">
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
              <p>スコア: {item.score && item.score > 0 ? item.score : '―'}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default function SupplementRankingPage() {
  const [activeTab, setActiveTab] = useState<'bcaa'|'eaa'>('bcaa');
  const [bcaaItems, setBcaaItems] = useState<ProductItem[]>([]);
  const [eaaItems,  setEaaItems]  = useState<ProductItem[]>([]);
  const [loading,   setLoading]    = useState({ bcaa: true, eaa: true });
  const [error,     setError]      = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    (async () => {
      try {
        setError(null);
        const [r1, r2] = await Promise.all([
          fetch('/api/supplements?type=bcaa&sort=score', { cache: 'no-store', signal: ac.signal }),
          fetch('/api/supplements?type=eaa&sort=score',  { cache: 'no-store', signal: ac.signal }),
        ]);
        const [d1, d2] = await Promise.all([r1.json(), r2.json()]);
        setBcaaItems(Array.isArray(d1) ? d1 : []);
        setEaaItems(Array.isArray(d2) ? d2 : []);
      } catch (e) {
        console.error('supplements load failed:', e);
        setError('読み込みに失敗しました。時間をおいて再度お試しください。');
      } finally {
        setLoading({ bcaa: false, eaa: false });
      }
    })();
    return () => ac.abort();
  }, []);

  const items = activeTab === 'eaa' ? eaaItems : bcaaItems;
  const periodLabel = useMemo(() => fmtRangeFromItems(items, '直近30日'), [items]);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-1 text-center">
        {periodLabel} サプリメント ランキング
      </h1>
      <p className="text-xs text-gray-500 text-center mb-6">（A方式：直近30日更新ぶん）</p>

      <p className="text-sm text-gray-500 text-center mb-6">
        <Link href="/about#score" className="underline hover:text-green-700">
          SuppBaseスコアとは？
        </Link>
      </p>

      <div className="flex justify-center mb-6 gap-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'bcaa' | 'eaa')}
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

      {error && <p className="text-center text-red-500 mb-4">{error}</p>}
      <RankingSection items={items} loading={activeTab === 'eaa' ? loading.eaa : loading.bcaa} />
    </main>
  );
}
