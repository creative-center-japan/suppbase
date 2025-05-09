export default function AboutPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 space-y-12">
      <section>
        <h1 className="text-4xl font-bold text-green-700 mb-4">SuppBaseとは</h1>
        <p className="text-gray-700 leading-relaxed text-lg">
          SuppBaseは、プロテイン・サプリメントに関するデータを整理・比較し、  
          より「自分に合った選択」をサポートするために作られたデータベース型メディアです。  
          Amazonなどの情報を元に、ランキング形式で情報を整理しつつ、  
          翻訳記事や運営者の知見も交えながらコンテンツを展開しています。
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">このサイトの使い方</h2>
        <ul className="list-disc list-inside text-gray-700 space-y-2">
          <li>日本と海外のプロテイン・サプリランキングを閲覧</li>
          <li>翻訳記事やレビューで情報収集</li>
          <li>商品リンクから直接Amazonへアクセス（アフィリエイト付き）</li>
        </ul>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">SuppBaseスコアについて</h2>
        <p className="text-gray-700 mb-4 text-lg">
          SuppBaseでは、価格の動きや売れ筋、レビューの反応など複数の要素をもとに、注目度の高い商品をピックアップする独自スコアを導入しています。
        </p>
        <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
スコア = 複数のファクターを独自の重みで組み合わせた数値
        </pre>
        <p className="text-gray-700 leading-relaxed">
          ・価格の下落：直近の価格変化をベースに、動きの多さや注目度を数値化しています。<br />
          ・売れ筋ランク：Amazonカテゴリ内での販売状況も加味しています（順位が低いほど人気）。<br />
          ・レビュー：件数や評価スコアも一部参考にしながら判断しています。<br />
          ・スコアが高いほど「注目されていて売れている可能性が高い商品」と判断されます。
        </p>
        <p className="text-gray-700 mt-4">
          また、価格が取得できなかった商品に対しては過去の平均価格などをもとに参考価格を補完表示しています。ドロップ回数については前月比の変化も表示され、商品の「動き」も一目で確認できるようになっています。
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-green-700 mb-2">運営について</h2>
        <p className="text-gray-700 leading-relaxed text-lg">
          SuppBaseは、筋トレ愛好家であり、健康志向とデータ分析が趣味の管理人が  
          情熱を注いで運営しているパーソナルプロジェクトです。  
          自らトレーニングを続けながら、最新情報を収集・検証し、  
          「好き」と「役立つ」を掛け合わせたコンテンツ作りを目指しています。  
          将来的にはフィットネスをもっと気軽に楽しめる環境を作れたら最高ですね💪
        </p>
      </section>

      <section className="mt-10 border-t pt-8">
        <h2 className="text-2xl font-semibold text-green-700 mb-2">プライバシー・ポリシーと免責事項</h2>

        <h3 className="text-xl font-bold mt-6 mb-1">個人情報の利用目的</h3>
        <p className="text-gray-700 mb-2">
          当サイトでは、お問い合わせやコメントの際に氏名、メールアドレスなどの個人情報をご登録いただく場合がございます。
          これらの個人情報は質問に対する回答や、必要な情報を電子メール等で連絡するために利用するものであり、それ以外の目的では利用しません。
        </p>

        <h3 className="text-xl font-bold mt-6 mb-1">Amazonアソシエイトについて</h3>
        <p className="text-gray-700 mb-2">
          当サイトは、Amazon.co.jp を宣伝しリンクすることによって、紹介料を獲得できるアフィリエイトプログラム「Amazonアソシエイト・プログラム」の参加者です。
        </p>

        <h3 className="text-xl font-bold mt-6 mb-1">Cookieについて</h3>
        <p className="text-gray-700 mb-2">
          当サイトでは、一部のコンテンツにおいてCookie（クッキー）を利用しています。
          Cookieには氏名やメールアドレスなど、個人を特定する情報は含まれません。
          ブラウザの設定でCookieを無効にすることも可能です。
        </p>

        <h3 className="text-xl font-bold mt-6 mb-1">免責事項</h3>
        <p className="text-gray-700">
          当サイトで掲載している情報は、正確性や安全性を保証するものではありません。
          掲載情報のご利用については、すべてご自身の責任でお願いいたします。
        </p>
      </section>
    </main>
  );
}
