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
  monthlySold?: number | null;
  salesRankDrops30?: number | null;
  salesRankDrops90?: number | null;
  salesRankDrops180?: number | null;
};

function getYearMonth() {
  const d = new Date();
  return `${d.getFullYear()}年${d.getMonth() + 1}月`;
}

export default function SupplementRankingPage() {
  const [items, setItems] = useState<RankingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const ym = getYearMonth();

  useEffect(() => {
    setLoading(true);

    fetch('/api/ranking/japan/supplement?limit=10', { cache: 'no-store' })
      .then(res => res.json())
      .then(data => setItems(Array.isArray(data.items) ? data.items : []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold text-center mb-6">
        サプリメントランキング【{ym}】
      </h1>

      <p className="text-center text-sm text-gray-500 mb-6">
        ※ 価格・在庫情報は変動します。最新情報は Amazon 商品ページをご確認ください。
      </p>

      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-8 text-sm text-gray-700 leading-relaxed">
        このランキングは、主に
        <span className="font-semibold">直近30日のランキング変動回数</span>と
        <span className="font-semibold">月間販売数の目安</span>
        をもとに整理しています。
        <br />
        最近よく売れている商品や、一定の販売数がある人気商品が上位に表示されやすい仕組みになっています。
      </div>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}