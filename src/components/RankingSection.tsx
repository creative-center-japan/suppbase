'use client';

import Image from 'next/image';
import Link from 'next/link';

/**
 * ランキング表示用の型
 */
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
      <div className="text-center text-gray-500 py-12">
        データを読み込み中です。少しお待ちください…
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="text-center text-gray-500 py-12">
        表示できるデータがありません。
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {items.map((item) => {
        // 画像フォールバック（DBに無い場合）
        const imageSrc =
          item.imageUrl ??
          `https://images-na.ssl-images-amazon.com/images/P/${item.asin}.jpg`;

        // 順位カラー
        const rankColor =
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
            className="flex gap-4 border rounded-xl p-4 items-center"
          >
            {/* ランク */}
            <div
              className={`text-white font-bold text-lg w-10 h-10 flex items-center justify-center rounded-full ${rankColor}`}
            >
              {item.rank}
            </div>

            {/* 画像 */}
            <div className="w-20 h-20 relative flex-shrink-0">
              <Image
                src={imageSrc}
                alt={item.title}
                fill
                className="object-contain rounded"
              />
            </div>

            {/* 情報 */}
            <div className="flex-1">
              <h3 className="font-semibold text-sm leading-snug mb-1">
                {item.title}
              </h3>
              <p className="text-xs text-gray-500 mb-1">{item.brand}</p>

              <div className="text-sm">
                {item.price !== null ? (
                  <span className="font-bold">
                    ¥{item.price.toLocaleString()}
                  </span>
                ) : (
                  <span className="text-gray-400">価格取得中</span>
                )}
              </div>

              <div className="text-xs text-gray-500 mt-1">
                {item.rating !== null ? (
                  <>
                    ★ {item.rating}（{item.reviewCount ?? 0}件）
                  </>
                ) : (
                  <>レビュー情報 取得中</>
                )}
              </div>
            </div>

            {/* Amazon */}
            <Link
              href={item.affiliateUrl}
              target="_blank"
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm whitespace-nowrap"
            >
              Amazonで見る
            </Link>
          </div>
        );
      })}
    </div>
  );
}
