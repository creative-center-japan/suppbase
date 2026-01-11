export default function AboutPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 space-y-12">
      <section>
        <h1 className="text-4xl font-bold text-green-700 mb-4">
          SuppBaseとは
        </h1>
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

      {/* ★ ランキング説明 */}
      <section id="ranking">
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          SuppBaseスコアについて
        </h2>

        <p className="text-gray-700 leading-relaxed mb-4 text-lg">
          SuppBaseでは、Keepaが取得しているAmazonの公開データをもとに、
          世の中で注目されている商品や、最近よく動いている商品の傾向を
          分かりやすく整理しています。
        </p>

        <p className="text-gray-700 leading-relaxed mb-4">
          売れ筋ランキングの推移や価格の変化、レビュー情報などを組み合わせることで、
          「最近よく見かける商品」や
          「いま選ばれていそうな商品」を
          見つけやすくするための指標としてご覧いただけます。
        </p>

        <div className="bg-gray-100 p-4 rounded text-sm leading-relaxed">
          ・売れ筋ランキングの位置や変動：人気の流れを把握するための目安<br />
          ・価格の変化：値下げや価格の動きがあった商品を見つけるための情報<br />
          ・レビュー情報：評価や件数の傾向を、判断材料のひとつとして参照
        </div>

        <p className="text-gray-700 mt-4">
          これらの情報をもとに表示しているランキングやスコアは、
          世の中で注目されていたり、実際によく見られている商品を
          ランキング形式で分かりやすく整理したものです。
          <br />
          商品選びのきっかけとして、
          「ちょっと見てみようかな」と思える材料を提供することを目的としています。
        </p>

        <p className="text-gray-700 mt-2">
          なお、取得タイミングやデータ状況によっては、
          一部の価格やレビュー情報が表示されない場合があります。
          その際は、過去に取得したデータを参考として表示することがありますので、
          あらかじめご了承ください。
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">
          運営について
        </h2>
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
          掲載している情報は、正確性や効果を保証するものではありません。
          商品の選択・購入については、
          ご自身の判断と責任のもとでお願いいたします。
        </p>
      </section>
    </main>
  );
}
