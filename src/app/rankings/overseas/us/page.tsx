// healthy-site\suppbase\src\app\rankings\overseas\us\page.tsx

'use client';

import { useEffect, useState } from 'react';
import RankingSection from '@/components/RankingSection';

function getYearMonth() {
  const d = new Date();
  return `${d.getFullYear()}年${d.getMonth() + 1}月`;
}

export default function USProteinRankingPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const ym = getYearMonth();

  useEffect(() => {
    setLoading(true);

    fetch('/api/ranking?type=whey&locale=us&limit=10', {
      cache: 'no-store',
    })
      .then(r => r.json())
      .then(d => setItems(Array.isArray(d.items) ? d.items : []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-2 text-center">
        US プロテインランキング【{ym}】
      </h1>

      <p className="text-center text-sm text-gray-500 mb-6">
        ※ 本ランキングは米国 Amazon の公開データをもとに集計しています。
        価格・在庫・レビュー情報は変動するため、最新情報は
        Amazon.com の商品ページをご確認ください。
      </p>

      <RankingSection items={items} loading={loading} />
    </main>
  );
}
