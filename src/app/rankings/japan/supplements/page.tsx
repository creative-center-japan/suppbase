// healthy-site\src\app\rankings\japan\supplements\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection from '@/components/RankingSection';
import type { RankingItemLite } from '../protein/page';

export default function SupplementRankingPage() {
  const [items, setItems] = useState<RankingItemLite[]>([]);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch('/api/ranking?type=supplement', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        if (cancelled) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
        setDescription(typeof data?.description === 'string' ? data.description : '');
      })
      .catch(() => {
        if (cancelled) return;
        setItems([]);
        setDescription('');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-6 text-center">
        サプリメント ランキング
      </h1>

      {description && (
        <div className="text-center mb-8 space-y-2">
          <p className="text-sm text-gray-600">{description}</p>
          <a
            href="/about#score"
            className="inline-flex items-center gap-1 text-sm font-semibold text-green-700 hover:text-green-800 underline underline-offset-4"
          >
            スコアについて詳しく見る →
          </a>
        </div>
      )}

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
