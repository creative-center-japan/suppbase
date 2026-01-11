// healthy-site\src\components\RankingSection.tsx

'use client';

import Image from 'next/image';

export type RankingItem = {
  rank: number;
  asin: string;
  title: string;
  brand: string;
  price: number | null;
  score?: number | null;
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
  // ★ 読み込み中表示（文言をやさしく）
  if (loading) {
    return (
      <div className="text-center text-gray-500 py-10 space-y-2">
        <p>ランキングを読み込んでいます。</p>
        <p className="text-sm">しばらくお待ちください。</p>
      </div>
    );
  }

  // ★ データなし
  if (!items.length) {
    return (
      <p className="text-center text-gray-400 py-8">
        表示できるデータがありません。
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {items.map(item => (
        <div
          key={item.asin}
          className={`p-4 rounded-xl shadow-sm border flex gap-4 min-h-[132px]
            ${
              item.rank === 1
                ? 'border-yellow-400 border-2'
                : item.rank === 2
                ? 'border-gray-400 border-2'
                : item.rank === 3
                ? 'border-orange-400 border-2'
                : 'border-gray-200'
            }`}
        >
          {/* 左：画像 */}
          <Image
            src={item.imageUrl || '/no-image.png'}
            alt={item.title}
            width={96}
            height={96}
            className="object-contain rounded"
            unoptimized
          />

          {/* 中央：情報 */}
          <div className="flex-1 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-semibold">
                #{item.rank} {item.title}
              </h3>

              <p className="text-sm text-gray-600">{item.brand}</p>

              <div className="flex items-center gap-3 mt-2">
                <span className="text-xl font-bold">
                  {item.price != null
                    ? `¥${item.price.toLocaleString()}`
                    : '―'}
                </span>

                {item.score != null && (
                  <span
                    className={`px-2 py-0.5 rounded-full text-sm font-semibold
                      ${
                        item.score >= 80
                          ? 'bg-green-100 text-green-700'
                          : item.score >= 65
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                  >
                    スコア {item.score}
                  </span>
                )}
              </div>

              {/* レビュー表示 */}
              <div className="flex items-center gap-1 text-sm mt-1 min-h-[20px]">
                {item.rating != null ? (
                  <>
                    <span className="text-yellow-500">
                      {'★'.repeat(Math.floor(item.rating))}
                    </span>
                    <span className="text-gray-500">
                      {item.rating.toFixed(1)}（{item.reviewCount ?? 0}）
                    </span>
                  </>
                ) : (
                  <span className="text-gray-300">
                    ★★★★★ ―（―）
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 右：CTA */}
          <div className="flex items-end">
            <a
              href={item.affiliateUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center
                         rounded-md bg-green-600 px-4 py-2
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
