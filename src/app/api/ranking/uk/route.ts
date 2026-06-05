// suppbase/src/app/rankings/overseas/uk/page.tsx

export const dynamic = 'force-dynamic';

type RankingItem = {
  rank: number;
  asin: string;
  title: string;
  brand: string;
  price: number | null;
  score: number | null;
  imageUrl: string | null;
  monthlySold: number;
  salesRankDrops30: number;
  salesRankDrops90: number;
  salesRankDrops180: number;
  proteinType: string | null;
  affiliateUrl: string;
};

async function getRanking(): Promise<RankingItem[]> {
  try {
    const baseUrl =
      process.env.NEXT_PUBLIC_SITE_URL ??
      'https://suppbase.creative-center-j.com';

    const res = await fetch(`${baseUrl}/api/ranking/uk?limit=20`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      return [];
    }

    const json = await res.json();
    return Array.isArray(json.items) ? json.items : [];
  } catch (e) {
    console.error('[UK ranking page error]', e);
    return [];
  }
}

export default async function OverseasUKPage() {
  const items = await getRanking();

  return (
    <main className="min-h-screen bg-white px-4 py-16">
      <div className="mx-auto max-w-5xl text-center">
        <p className="mb-3 text-sm tracking-widest text-gray-400">
          OVERSEAS RANKING
        </p>

        <h1 className="mb-4 text-4xl font-bold text-gray-900">
          GB United Kingdom
        </h1>

        <p className="mb-8 text-gray-600">
          イギリス市場のサプリ・プロテインランキングです。
        </p>

        {items.length === 0 ? (
          <div className="mx-auto max-w-xl rounded-lg border border-dashed border-gray-300 p-8 text-gray-500">
            UKランキングデータがまだありません。
            <br />
            UK商品の収集が完了すると、ここにランキングが表示されます。
          </div>
        ) : (
          <div className="space-y-4 text-left">
            {items.map((item) => (
              <div
                key={item.asin}
                className="flex gap-4 rounded-xl border p-4"
              >
                <div className="w-12 text-xl font-bold">#{item.rank}</div>

                {item.imageUrl ? (
                  <img
                    src={item.imageUrl}
                    alt={item.title}
                    className="h-24 w-24 object-contain"
                  />
                ) : (
                  <div className="flex h-24 w-24 items-center justify-center rounded bg-gray-100 text-xs text-gray-400">
                    No Image
                  </div>
                )}

                <div className="flex-1">
                  <h2 className="font-semibold">{item.title}</h2>
                  <p className="text-sm text-gray-500">{item.brand}</p>
                  <p className="text-sm">Score: {item.score ?? '-'}</p>
                  <p className="text-sm">
                    価格: {item.price ? `£${(item.price / 100).toFixed(2)}` : '-'}
                  </p>

                  <a
                    href={item.affiliateUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-block text-sm underline"
                  >
                    Amazon UKで見る
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}