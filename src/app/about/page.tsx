export default function AboutPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 space-y-12">
      <section>
        <h1 className="text-4xl font-bold text-green-700 mb-4">SuppBaseとは</h1>
        <p className="text-gray-700 leading-relaxed text-lg">
          SuppBaseは、プロテイン・サプリメントに関する情報を整理・比較しながら、
          「いまどんな商品が注目されているのか」を把握しやすくするための
          データベース型メディアです。
          <br />
          Amazonなどで公開されている情報をもとにランキング形式で整理しつつ、
          翻訳記事や運営者の視点も交えながらコンテンツを展開しています。
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          このサイトの使い方
        </h2>
        <ul className="list-disc list-inside text-gray-700 space-y-2">
          <li>プロテイン・サプリメントのランキングをチェック</li>
          <li>価格や傾向を見ながら気になる商品を比較</li>
          <li>商品ページからそのままAmazonで詳細を確認</li>
        </ul>
      </section>

      {/* ★ ここから差し替え */}
      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          ランキングの見方について
        </h2>

        <p className="text-gray-700 mb-4 text-lg">
          SuppBaseのランキングは、実際の「購入数」や「売上金額」を直接集計したものではありません。
          Amazonではそうした数値は公開されていないため、
          公開されているデータをもとに、商品の動きや注目度を整理しています。
        </p>

        <p className="text-gray-700 leading-relaxed mb-4">
          ランキングの算出には、Keepaが取得しているAmazonの公開情報
          （売れ筋ランキングの推移、価格の変化、レビュー情報など）を主に利用しています。
          「最近よく動いている商品」や「相対的に注目されていそうな商品」を
          見つけやすくするための参考指標、というイメージです。
        </p>

        <div className="bg-gray-100 p-4 rounded text-sm leading-relaxed">
          ・売れ筋ランキングの位置や変動：人気の傾向を見るための目安<br />
          ・価格の変化：値下げや価格の動きがあった商品を把握するための情報<br />
          ・レビュー情報：件数や評価の傾向を、補助的な判断材料として参照
        </div>

        <p className="text-gray-700 mt-4">
          これらの情報をもとに表示しているランキングやスコアは、
          「どの商品が良いか」を断定するものではありません。
          あくまで、商品選びのヒントとして
          「ちょっと見てみようかな」と思える材料を提供することを目的としています。
        </p>

        <p className="text-gray-700 mt-2">
          なお、タイミングによっては価格情報が取得できない場合があります。
          その際は、過去の取得データなどを参考表示することがありますので、
          あらかじめご了承ください。
        </p>
      </section>
      {/* ★ 差し替えここまで */}

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">運営について</h2>
        <p className="text-gray-700 leading-relaxed text-lg">
          SuppBaseは、筋トレが好きでデータを見るのも好きな個人が、
          趣味と実益を兼ねて運営しているパーソナルプロジェクトです。
          <br />
          実際にトレーニングを続けながら、
          「調べるのがちょっと面倒なところ」を少しでも楽にできたら、
          という気持ちで更新しています。
        </p>
      </section>

      <section className="mt-10 border-t pt-8">
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          プライバシー・ポリシーと免責事項
        </h2>

        <h3 className="text-xl font-bold mt-6 mb-1">Amazonアソシエイトについて</h3>
        <p className="text-gray-700 mb-2">
          当サイトは、Amazon.co.jpを宣伝しリンクすることによって、
          紹介料を獲得できるアフィリエイトプログラム
          「Amazonアソシエイト・プログラム」の参加者です。
        </p>

        <h3 className="text-xl font-bold mt-6 mb-1">免責事項</h3>
        <p className="text-gray-700">
          掲載している情報は、正確性や効果を保証するものではありません。
          商品の選択・購入については、
          ご自身の判断と責任のもとでお願いいたします。
        </p>
      </section>
    </main>
  );
}
