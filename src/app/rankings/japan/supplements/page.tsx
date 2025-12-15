'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const tabs = [
  { id: 'bcaa', label: 'BCAA' },
  { id: 'eaa', label: 'EAA' },
];

type ProductItem = {
  rank: number; // API由来だが、UIでは使わず再採番
  title: string;
  asin: string;
  brand: string;
  price: number | null;
  imageUrl: string | null;
  dropRate: number | null;
  dropRateDiff: number | null;
  score: number | null;
  affiliateUrl: string;
};

/* ===============================
   ★ 除外ロジック
   =============================== */

// BCAAでは「プロテイン系」を強く除外
function isPureBCAA(title: string) {
  const t = title.toLowerCase();
  if (
    t.includes('プロテイン') ||
    t.includes('protein') ||
    t.includes('ホエイ') ||
    t.includes('whey') ||
    t.includes('wpc') ||
    t.includes('wpi')
  ) {
    return false;
  }
  return t.includes('bcaa');
}

// EAAは除外を緩める（飲料だけ弾く）
function isPureEAA(title: string) {
  const t = title.toLowerCase();
  if (t.includes('ドリンク') || t.includes('飲料')) {
    return false;
  }
  return t.includes('eaa');
}

/* ===============================
   RankingSection
   =============================== */
const RankingSection = (
  { items, loading }: { items: ProductItem[]; loading?: boolean }
) => {
  if (loading) return <p className="text-center text-gray-400">ランキング読み込み中...</p>;
  if (!items.length) return <p className="text-center text-gray-400">データがありません</p>;

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

/* ===============================
   Page
   =============================== */
export default function SupplementRankingPage() {
  const [activeTab, setActiveTab] = useState<'bcaa' | 'eaa'>('bcaa');
  const [bcaaItems, setBcaaItems] = useState<ProductItem[]>([]);
  const [eaaItems, setEaaItems] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState({ bcaa: true, eaa: true });
  const [error, setError] = useState<string | null>(null);
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
    const ac = new AbortController();
    (async () => {
      try {
        setError(null);
        const [r1, r2] = await Promise.all([
          fetch('/api/supplements?type=bcaa&sort=score', { cache: 'no-store', signal: ac.signal }),
          fetch('/api/supplements?type=eaa&sort=score',  { cache: 'no-store', signal: ac.signal }),
        ]);
        const [d1, d2] = await Promise.all([r1.json(), r2.json()]);

        // ★ 除外ロジックをここで適用
        setBcaaItems(
          (Array.isArray(d1) ? d1 : []).filter(item => isPureBCAA(item.title))
        );
        setEaaItems(
          (Array.isArray(d2) ? d2 : []).filter(item => isPureEAA(item.title))
        );
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
  const isLoading = activeTab === 'eaa' ? loading.eaa : loading.bcaa;

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-1 text-center">
        {titleMonth ? `${titleMonth} サプリメント ランキング` : 'サプリメント ランキング'}
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
      <RankingSection items={items} loading={isLoading} />
    </main>
  );
}
