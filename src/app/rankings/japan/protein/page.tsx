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
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);

    fetch(
      new URL(
        `/api/ranking?type=${activeTab}&sort=score`,
        window.location.origin
      ),
      { cache: 'no-store' }
    )
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
      <h1 className="text-3xl font-bold mb-6 text-center">
        プロテイン ランキング
      </h1>

      {/* タブ切り替え */}
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

      {description && (
        <p className="text-sm text-gray-600 mb-4 text-center">
          {description}
        </p>
      )}

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
