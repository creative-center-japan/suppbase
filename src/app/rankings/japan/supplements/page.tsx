// healthy-site\src\app\rankings\japan\supplements\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection from '@/components/RankingSection';

type RankingItemLite = {
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
  const [items, setItems] = useState<RankingItemLite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    fetch('/api/ranking/supplement?limit=10', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        setItems(Array.isArray(data.items) ? data.items : []);
      })
      .catch(() => {
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-center mb-6">
        サプリメントランキング
      </h1>

      <p className="text-center text-sm text-gray-500 mb-6">
        ※ 価格・在庫・レビュー情報は変動します。最新の販売価格・詳細は
        各商品リンク先の Amazon ページをご確認ください。
      </p>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
