//healthy-site\src\app\rankings\japan\protein\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection, { RankingItem } from '@/components/RankingSection';

type ProteinTab = 'whey' | 'soy' | 'isolate';

const tabs: { id: ProteinTab; label: string }[] = [
  { id: 'whey', label: 'ホエイ' },
  { id: 'soy', label: 'ソイ' },
  { id: 'isolate', label: 'アイソレート（WPI）' },
];

export default function ProteinRankingPage() {
  const [activeTab, setActiveTab] = useState<ProteinTab>('whey');
  const [items, setItems] = useState<RankingItem[]>([]);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    fetch(`/api/ranking?type=${activeTab}`, { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        setItems(Array.isArray(data.items) ? data.items : []);
        setDescription(data.description ?? '');
      })
      .catch(() => {
        setItems([]);
        setDescription('');
      })
      .finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4 text-center">
        プロテイン ランキング
      </h1>

      {/* タブ */}
      <div className="flex justify-center mb-4 gap-2">
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

      {/* 説明＋リンク */}
      {description && (
        <div className="text-center mb-6 space-y-2">
          <p className="text-sm text-gray-600">
            {description}
          </p>
          <a
            href="/about#ranking"
            className="inline-block text-sm text-green-700 font-medium hover:underline"
          >
            スコアについて詳しく見る →
          </a>
        </div>
      )}

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
