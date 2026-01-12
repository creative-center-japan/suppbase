'use client';

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
};

type Props = {
  items: RankingItem[];
  loading: boolean;
};

const fallbackImage = '/no-image.png';

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

  // ★ 10位までに制限
  const displayItems = items.slice(0, 10);

  return (
    <div className="space-y-4">
      {displayItems.map(item => {
        const isTop1 = item.rank === 1;
        const isTop2 = item.rank === 2;
        const isTop3 = item.rank === 3;

        const borderColor = isTop1
          ? 'border-green-600'
          : isTop2
          ? 'border-green-500'
          : isTop3
          ? 'border-green-400'
          : 'border-green-200';

        const rankBg = isTop1
          ? 'bg-green-700'
          : isTop2
          ? 'bg-green-600'
          : isTop3
          ? 'bg-green-500'
          : 'bg-green-400';

        // ---------- 安全な値整形 ----------
        const hasRating =
          typeof item.rating === 'number' && item.rating >= 0;

        const ratingText = hasRating
          ? `★${item.rating!.toFixed(1)}`
          : '—';

        const reviewText =
          typeof item.reviewCount === 'number'
            ? `${item.reviewCount.toLocaleString()}件`
            : '—';

        const priceText =
          typeof item.price === 'number' && item.price > 0
            ? `¥${item.price.toLocaleString()}`
            : '価格情報取得中';

        return (
          <div
            key={item.asin}
            className={`flex items-center gap-4 border-2 ${borderColor} rounded-xl p-5 bg-white`}
          >
            {/* 順位 */}
            <div
              className={`flex items-center justify-center text-white font-bold text-lg w-10 h-10 rounded-full ${rankBg}`}
            >
              {item.rank}
            </div>

            {/* 画像 */}
            <div className="w-28 h-28 flex-shrink-0 bg-green-50 rounded">
              <img
                src={item.imageUrl || fallbackImage}
                alt={item.title}
                className="w-full h-full object-contain rounded"
              />
            </div>

            {/* 情報 */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 leading-snug line-clamp-2">
                {item.title}
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
                <span className="flex items-center gap-1 text-green-600">
                  <span className="font-semibold">{ratingText}</span>
                  <span className="text-gray-500">
                    ({reviewText})
                  </span>
                </span>

                {/* スコア（仮） */}
                <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded-full text-xs font-semibold">
                  SuppBaseスコア 集計中
                </span>
              </div>
            </div>

            {/* ボタン */}
            <div className="flex-shrink-0">
              <a
                href={item.affiliateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-green-600 hover:bg-green-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition"
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
