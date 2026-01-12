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
};

export default function SupplementRankingPage() {
  const [items, setItems] = useState<RankingItemLite[]>([]);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);

    fetch('/api/ranking?type=supplement&limit=10', { cache: 'no-store' })
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
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-2 text-center">
        サプリメントランキング【2026年1月】
      </h1>

      {/* 注記 */}
      <p className="text-center text-sm text-gray-500 mb-6">
        ※ 価格・在庫・レビュー情報は変動します。最新の販売価格・詳細は
        各商品リンク先の Amazon ページをご確認ください。
      </p>

      {description && (
        <div className="text-center mb-8 space-y-2">
          <p className="text-sm text-gray-600">{description}</p>
          <a
            href="/about#score"
            className="inline-flex items-center gap-1 text-sm font-semibold text-green-700 hover:text-green-800 underline underline-offset-4"
          >
            SuppBaseスコアについて詳しく見る →
          </a>
        </div>
      )}

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
