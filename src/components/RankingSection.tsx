// healthy-site\src\components\RankingSection.tsx

'use client';

import Image from 'next/image';

export type RankingItem = {
  rank: number;
  asin: string;
  title: string;
  brand: string;
  price: number | null;
  score: number | null;
  rating?: number | null;
  reviewCount?: number | null;
  imageUrl: string | null;
  affiliateUrl: string;
};

export default function RankingSection({
  items,
  loading,
}: {
  items: RankingItem[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <p className="text-center text-gray-400 py-8">
        ランキング読み込み中…
      </p>
    );
  }

  if (!items.length) {
    return (
      <p className="text-center text-gray-400 py-8">
        データがありません
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {items.map(item => (
        <div
          key={item.asin}
          className={`p-4 rounded-xl shadow-sm hover:shadow-md transition flex gap-4 ${
            item.rank === 1
              ? 'border-2 border-yellow-400'
              : item.rank === 2
              ? 'border-2 border-gray-400'
              : item.rank === 3
              ? 'border-2 border-orange-400'
              : 'border border-gray-200'
          }`}
        >
          {/* 商品画像 */}
          <Image
            src={
              item.imageUrl && item.imageUrl.startsWith('http')
                ? item.imageUrl
                : '/no-image.png'
            }
            alt={item.title}
            width={96}
            height={96}
            className="object-contain rounded"
            unoptimized
          />

          {/* 右側情報 */}
          <div className="flex-1">
            <h3 className="text-lg font-semibold">
              #{item.rank} {item.title}
            </h3>

            <p className="text-sm text-gray-600">{item.brand}</p>

            {/* 価格・スコア */}
            <div className="flex items-center gap-4 mt-2">
              <span className="text-xl font-bold text-gray-900">
                {item.price != null
                  ? `¥${item.price.toLocaleString()}`
                  : '―'}
              </span>

              <span className="px-2 py-0.5 rounded-full text-sm bg-gray-100 text-gray-700">
                スコア {item.score ?? '―'}
              </span>
            </div>

            {/* レビュー */}
            {item.rating != null && (
              <div className="flex items-center gap-1 text-sm text-yellow-500 mt-1">
                {'★'.repeat(Math.floor(item.rating))}
                <span className="text-gray-600 ml-1">
                  ({item.reviewCount ?? 0})
                </span>
              </div>
            )}

            {/* Amazonリンク */}
            <a
              href={item.affiliateUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center
                         rounded-md bg-green-600 px-4 py-2 mt-3
                         text-white text-sm font-semibold
                         hover:bg-green-700 transition"
            >
              Amazonで見る
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
