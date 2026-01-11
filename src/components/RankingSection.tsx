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

const fallbackImage = '/no-image.png'; // public/no-image.png を置く

export default function RankingSection({ items, loading }: Props) {
  if (loading) {
    return (
      <div className="text-center py-16 text-gray-500">
        データを読み込み中です。しばらくお待ちください。
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

  return (
    <div className="space-y-4">
      {items.map(item => {
        const isTop1 = item.rank === 1;
        const isTop2 = item.rank === 2;
        const isTop3 = item.rank === 3;

        const borderColor = isTop1
          ? 'border-yellow-400'
          : isTop2
          ? 'border-gray-400'
          : isTop3
          ? 'border-orange-400'
          : 'border-gray-200';

        const rankBg = isTop1
          ? 'bg-yellow-400'
          : isTop2
          ? 'bg-gray-400'
          : isTop3
          ? 'bg-orange-400'
          : 'bg-green-600';

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
            <div className="w-28 h-28 flex-shrink-0">
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

              <div className="mt-2 flex flex-wrap gap-2 text-sm">
                {/* 価格 */}
                <span className="text-green-700 font-semibold">
                  {item.price && item.price > 0
                    ? `¥${item.price.toLocaleString()}`
                    : '価格情報取得中'}
                </span>

                {/* レビュー */}
                <span className="text-gray-500">
                  {item.rating && item.reviewCount
                    ? `★${item.rating.toFixed(1)} (${item.reviewCount}件)`
                    : 'レビュー情報取得中'}
                </span>

                {/* スコア */}
                <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded text-xs font-medium">
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
