// healthy-site\src\app\rankings\japan\supplements\page.tsx

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

export default function SupplementRankingPage() {
  const [items, setItems] = useState<RankingItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    // 🔧 supplement 専用 API はまだ無いので暫定的に共通 API
    fetch('/api/ranking?limit=10', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        setItems(Array.isArray(data.items) ? data.items : []);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-center mb-6">
        サプリメントランキング
      </h1>

      <p className="text-center text-sm text-gray-500 mb-6">
        ※ 本ランキングは暫定表示です。後日、サプリ専用ランキングを追加予定です。
      </p>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
