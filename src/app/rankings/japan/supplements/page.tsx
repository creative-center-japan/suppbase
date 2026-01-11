// healthy-site\src\app\rankings\japan\supplements\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection, { RankingItem } from '@/components/RankingSection';

export default function SupplementRankingPage() {
  const [items, setItems] = useState<RankingItem[]>([]);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    fetch('/api/ranking?type=supplement', { cache: 'no-store' })
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
  }, []);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4 text-center">
        サプリメント ランキング
      </h1>

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
