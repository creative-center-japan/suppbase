// suppbase/src/app/rankings/overseas/uk/page.tsx

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
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

  const res = await fetch(`${baseUrl}/api/ranking/uk?limit=20`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    return [];
  }

  const json = await res.json();
  return json.items ?? [];
}

export default async function OverseasUKPage() {
  const items = await getRanking();

  return (
    <main className="min-h-screen bg-white px-4 py-10">
      <div className="mx-auto max-w-5xl">
        <p className="text-sm tracking-widest text-gray-400 mb-3">
          OVERSEAS RANKING
        </p>

        <h1 className="text-4xl font-bold mb-3">
          United Kingdom Protein Ranking
        </h1>

        <p className="text-gray-600 mb-8">
          英国Amazonの公開データをもとに、ランキング変動や販売傾向を整理しています。
        </p>

        {items.length === 0 ? (
          <div className="border border-dashed rounded-lg p-8 text-gray-500">
            UKランキングデータがまだありません。DB収集後に表示されます。
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <div
                key={item.asin}
                className="border rounded-xl p-4 flex gap-4 items-start"
              >
                <div className="text-2xl font-bold w-14">
                  #{item.rank}
                </div>

                {item.imageUrl ? (
                  <img
                    src={item.imageUrl}
                    alt={item.title}
                    className="w-24 h-24 object-contain"
                  />
                ) : (
                  <div className="w-24 h-24 bg-gray-100 rounded flex items-center justify-center text-xs text-gray-400">
                    No Image
                  </div>
                )}

                <div className="flex-1">
                  <h2 className="font-semibold text-lg mb-1">
                    {item.title}
                  </h2>

                  <p className="text-sm text-gray-500 mb-2">
                    {item.brand}
                  </p>

                  <div className="text-sm text-gray-700 space-y-1">
                    <p>価格: {item.price ? `£${(item.price / 100).toFixed(2)}` : '-'}</p>
                    <p>SuppBase Score: {item.score ?? '-'}</p>
                    <p>30日変動回数: {item.salesRankDrops30}</p>
                  </div>

                  <a
                    href={item.affiliateUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-3 text-sm underline"
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