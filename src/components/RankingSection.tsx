'use client';

import Image from 'next/image';
import Link from 'next/link';

export type RankingItem = {
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

type Props = {
  items: RankingItem[];
  loading?: boolean;
};

export default function RankingSection({ items, loading }: Props) {
  if (loading) {
    return (
      <div className="text-center text-gray-500 py-16">
        ランキングデータを読み込み中です。少しお待ちください…
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="text-center text-gray-500 py-16">
        表示できるデータがありません。
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {items.map((item) => {
        const imageSrc =
          item.imageUrl ??
          `https://images-na.ssl-images-amazon.com/images/P/${item.asin}.jpg`;

        // 順位ごとの色
        const rankStyle =
          item.rank === 1
            ? 'border-yellow-400 bg-yellow-50'
            : item.rank === 2
            ? 'border-gray-400 bg-gray-50'
            : item.rank === 3
            ? 'border-orange-400 bg-orange-50'
            : 'border-green-200 bg-white';

        const rankBadge =
          item.rank === 1
            ? 'bg-yellow-400'
            : item.rank === 2
            ? 'bg-gray-400'
            : item.rank === 3
            ? 'bg-orange-400'
            : 'bg-green-600';

        return (
          <div
            key={item.asin}
            className={`flex gap-6 items-center rounded-xl border-2 p-6 ${rankStyle}`}
          >
            {/* 順位 */}
            <div
              className={`w-12 h-12 rounded-full text-white font-bold text-lg flex items-center justify-center ${rankBadge}`}
            >
              {item.rank}
            </div>

            {/* 画像 */}
            <div className="w-28 h-28 relative flex-shrink-0">
              <Image
                src={imageSrc}
                alt={item.title}
                fill
                className="object-contain rounded"
              />
            </div>

            {/* 情報 */}
            <div className="flex-1">
              <h3 className="font-semibold text-base leading-snug mb-1">
                {item.title}
              </h3>
              <p className="text-sm text-gray-500 mb-2">{item.brand}</p>

              {/* 価格 */}
              <div className="text-lg font-bold text-green-700">
                {item.price !== null && item.price >= 0
                  ? `¥${item.price.toLocaleString()}`
                  : '価格情報 集計中'}
              </div>

              {/* レビュー */}
              <div className="text-sm text-gray-500 mt-1">
                {item.rating !== null ? (
                  <>
                    ★ {item.rating.toFixed(1)}（{item.reviewCount ?? 0}件）
                  </>
                ) : (
                  <>レビュー情報 取得中</>
                )}
              </div>

              {/* スコア */}
              <div className="text-xs text-green-600 mt-1">
                SuppBaseスコア：集計中
              </div>
            </div>

            {/* Amazon */}
            <Link
              href={item.affiliateUrl}
              target="_blank"
              className="bg-green-600 hover:bg-green-700 text-white px-5 py-3 rounded-md text-sm whitespace-nowrap font-semibold"
            >
              Amazonで見る
            </Link>
          </div>
        );
      })}
    </div>
  );
}
