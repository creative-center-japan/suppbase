// healthy-site\src\app\rankings\japan\supplements\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection, { RankingItem } from '@/components/RankingSection';

export default function SupplementRankingPage() {
  const [items, setItems] = useState<RankingItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    fetch(
      new URL('/api/ranking?type=bcaa&sort=score', window.location.origin),
      { cache: 'no-store' }
    )
      .then(res => res.json())
      .then(data => setItems(Array.isArray(data) ? data : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 text-center">
        サプリメント ランキング
      </h1>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
