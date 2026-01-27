//healthy-site\src\app\rankings\japan\protein\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection from '@/components/RankingSection';

type RankingItem = {
  rank: number;
  asin: string;
  title: string;
  brand: string;
  price: number | null;
  rating: number | null;
  reviewCount: number | null;
  imageUrl: string | null;
  affiliateUrl: string;
  score?: number | null;
};

function getYearMonth() {
  const d = new Date();
  return `${d.getFullYear()}年${d.getMonth() + 1}月`;
}

const TABS = [
  { id: 'wpi', label: 'WPI（アイソレート）' },
  { id: 'soy', label: 'ソイプロテイン' },
];

export default function ProteinRankingPage() {
  const [activeTab, setActiveTab] = useState<'wpi' | 'soy'>('wpi');
  const [items, setItems] = useState<RankingItem[]>([]);
  const [loading, setLoading] = useState(true);

  const ym = getYearMonth();

  useEffect(() => {
    setLoading(true);

    fetch(`/api/ranking?type=${activeTab}&limit=10`, {
      cache: 'no-store',
    })
      .then(r => r.json())
      .then(d => setItems(Array.isArray(d.items) ? d.items : []))
      .finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-2 text-center">
        プロテインランキング【{ym}】
      </h1>

      <p className="text-center text-sm text-gray-500 mb-6">
        ※ 価格・在庫・レビュー情報は変動します。最新情報は
        Amazon 商品ページをご確認ください。
      </p>

      {/* タブ */}
      <div className="flex justify-center gap-3 mb-6">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as 'wpi' | 'soy')}
            className={`px-4 py-2 rounded-full text-sm font-semibold border
              ${
                activeTab === tab.id
                  ? 'bg-green-600 text-white border-green-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
