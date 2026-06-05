// suppbase/src/app/rankings/overseas/uk/page.tsx

export const dynamic = 'force-dynamic';

export default function OverseasUKPage() {
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

        <div className="mx-auto max-w-xl rounded-lg border border-dashed border-gray-300 p-8 text-gray-500">
          UKランキングデータがまだありません。
          <br />
          UK商品の収集が完了すると、ここにランキングが表示されます。
        </div>
      </div>
    </main>
  );
}