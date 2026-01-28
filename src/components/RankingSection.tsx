'use client';
// healthy-site/suppbase/src/components/RankingSection.tsx

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

type Props = {
  items: RankingItem[];
  loading: boolean;
};

const fallbackImage = '/no-image.png';

/**
 * ★ Tailwind purge 対策
 * ここに class 名をベタ書きしておくことで
 * 本番ビルドでも確実に反映される
 */
const RANK_STYLE_MAP: Record<
  number,
  {
    border: string;
    bg: string;
    badge: string;
  }
> = {
  1: {
    border: 'border-yellow-500',
    bg: 'bg-yellow-100',
    badge: 'bg-yellow-500 text-white',
  },
  2: {
    border: 'border-gray-400',
    bg: 'bg-gray-100',
    badge: 'bg-gray-400 text-white',
  },
  3: {
    border: 'border-amber-700',
    bg: 'bg-amber-100',
    badge: 'bg-amber-600 text-white',
  },
};

export default function RankingSection({ items, loading }: Props) {
  if (loading) {
    return (
      <div className="text-center py-16 text-gray-500">
        データを読み込み中です…
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="text-center py-16 text-gray-500">
        表示できるデータがありません。
      </div>
    );
  }

  const displayItems = items.slice(0, 10);

  return (
    <div className="space-y-5">
      {displayItems.map(item => {
        const rankStyle = RANK_STYLE_MAP[item.rank];

        const borderColor = rankStyle?.border ?? 'border-gray-200';
        const bgColor = rankStyle?.bg ?? 'bg-white';
        const rankBg = rankStyle?.badge ?? 'bg-gray-200 text-gray-700';

        const ratingText =
          typeof item.rating === 'number' && item.rating >= 0
            ? `★${item.rating.toFixed(1)}`
            : '★—';

        const reviewText =
          typeof item.reviewCount === 'number'
            ? `${item.reviewCount.toLocaleString()}件`
            : '—件';

        const priceText =
          typeof item.price === 'number' && item.price > 0
            ? `¥${item.price.toLocaleString()}`
            : '価格情報取得中';

        const scoreText =
          typeof item.score === 'number'
            ? item.score.toLocaleString()
            : null;

        return (
          <div
            key={item.asin}
            className={`flex items-center gap-4 border-2 ${borderColor} ${bgColor}
                        rounded-xl p-5 shadow-sm`}
          >
            {/* 順位バッジ */}
            <div
              className={`flex items-center justify-center font-bold text-lg
                          w-10 h-10 rounded-full ${rankBg}`}
            >
              {item.rank}
            </div>

            {/* 画像 */}
            <div className="w-28 h-28 flex-shrink-0 bg-white rounded border">
              <img
                src={item.imageUrl || fallbackImage}
                alt={item.title}
                className="w-full h-full object-contain rounded"
              />
            </div>

            {/* 情報 */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 leading-snug line-clamp-2">
                #{item.rank} {item.title}
              </h3>

              <p className="text-sm text-gray-500 mt-1">
                {item.brand}
              </p>

              <div className="mt-3 flex flex-wrap gap-3 text-sm items-center">
                {/* 価格 */}
                <span className="text-green-700 font-semibold">
                  {priceText}
                </span>

                {/* レビュー */}
                <span className="flex items-center gap-1 text-green-700">
                  <span className="font-semibold">{ratingText}</span>
                  <span className="text-gray-500">
                    ({reviewText})
                  </span>
                </span>

                {/* スコア */}
                {scoreText ? (
                  <span className="bg-green-100 text-green-800
                                   px-2 py-0.5 rounded-full
                                   text-xs font-bold">
                    SuppBaseスコア {scoreText}
                  </span>
                ) : (
                  <span className="bg-green-50 text-green-700
                                   px-2 py-0.5 rounded-full
                                   text-xs font-medium">
                    SuppBaseスコア 集計中
                  </span>
                )}
              </div>
            </div>

            {/* ボタン */}
            <div className="flex-shrink-0">
              <a
                href={item.affiliateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-green-600 hover:bg-green-700
                           text-white text-sm font-semibold
                           px-4 py-2 rounded-lg transition"
              >
                Amazonで見る
              </a>
            </div>
          </div>
        );
      })}
    </div>
  );
}
