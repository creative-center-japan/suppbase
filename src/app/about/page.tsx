export default function AboutPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 space-y-12">
      <section>
        <h1 className="text-4xl font-bold text-green-700 mb-4">
          SuppBaseとは
        </h1>
        <p className="text-gray-700 leading-relaxed text-lg">
          SuppBaseは、プロテインやサプリメントに関する商品情報を整理し、
          「いまどんな商品が動いているのか」「どの商品が比較的よく売れているのか」を
          つかみやすくするためのデータベース型メディアです。
          <br />
          Amazonで公開されている商品情報や、Keepaで取得できる公開データをもとに、
          ランキング形式で見やすく整理しています。
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          このサイトの使い方
        </h2>
        <ul className="list-disc list-inside text-gray-700 space-y-2">
          <li>プロテイン・サプリメントのランキングをチェックする</li>
          <li>価格や最近の動きを見ながら商品を比較する</li>
          <li>気になる商品はAmazonの商品ページで詳細を確認する</li>
        </ul>
      </section>

      <section id="ranking">
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          SuppBaseスコアについて
        </h2>

        <p className="text-gray-700 leading-relaxed mb-4">
          Amazonでは世界中で膨大な商品が販売されていますが、
          実際にどの商品がどれくらい売れているのかは
          サイト上からは分かりにくくなっています。
        </p>

        <p className="text-gray-700 leading-relaxed mb-4">
          SuppBaseでは、Amazon商品のデータを分析できる
          <strong>Keepa</strong>というデータサービスを利用し、
          商品の売れ方や動きを分かりやすく整理しています。
        </p>

        <div className="bg-gray-100 p-4 rounded text-sm leading-relaxed">
          ・直近30日のランキング変動回数：最近の売れ行きの目安<br />
          ・月間販売数の目安：販売規模の参考情報<br />
          ・価格情報：現在価格や価格の動き
        </div>

        <p className="text-gray-700 mt-4">
          これらのデータを組み合わせて、
          最近よく売れている可能性が高い商品が上位に来るよう
          整理したものが「SuppBaseスコア」です。
        </p>

        <p className="text-gray-700 mt-2">
          ランキングは、今どんな商品が注目されているのかを
          ざっくり把握するための参考情報としてご覧ください。
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          運営について
        </h2>
        <p className="text-gray-700 leading-relaxed text-lg">
          SuppBaseは、トレーニングやサプリメントに関心があり、
          商品比較やデータを見るのが好きな個人が運営しているパーソナルプロジェクトです。
          <br />
          実際に継続してトレーニングをしながら、
          「比較するのが少し面倒な商品情報を、できるだけ見やすく整理したい」
          という考えで更新しています。
        </p>
      </section>

      <section className="mt-10 border-t pt-8">
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          プライバシー・ポリシーと免責事項
        </h2>

        <h3 className="text-xl font-bold mt-6 mb-1">
          Amazonアソシエイトについて
        </h3>
        <p className="text-gray-700 mb-2">
          当サイトは、Amazon.co.jpを宣伝しリンクすることによって、
          紹介料を獲得できるアフィリエイトプログラム
          「Amazonアソシエイト・プログラム」の参加者です。
        </p>

        <h3 className="text-xl font-bold mt-6 mb-1">
          免責事項
        </h3>
        <p className="text-gray-700">
          掲載している情報は、公開データをもとに整理した参考情報であり、
          正確性・完全性・最新性を保証するものではありません。
          商品の選択や購入については、
          必ず販売元ページの内容をご確認のうえ、
          ご自身の判断と責任のもとでお願いいたします。
        </p>
      </section>
    </main>
  );
}