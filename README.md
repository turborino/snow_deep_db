# スキーリゾート積雪予測AI - Django版

AIが選択したスキーリゾートの未来の積雪量を月単位で予測するDjangoウェブアプリケーションです。

## 特徴

- 7つのスキー場の積雪量予測（野沢温泉、湯沢、白馬、軽井沢、菅平、草津、猪苗代）
- 11月〜4月の冬季月別予測
- 過去10シーズンとの比較グラフ表示
- モダンなBootstrapベースのUI
- Chart.jsによるインタラクティブなグラフ

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. データベースの初期化

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. スキー場マスターデータの登録

```bash
python manage.py setup_resorts
```

### 4. 管理者ユーザーの作成（任意）

```bash
python manage.py createsuperuser
```

### 5. 開発サーバーの起動

```bash
python manage.py runserver
```

アプリケーションは http://127.0.0.1:8000/ でアクセスできます。

## ファイル構成

```
Snow_Deep_Predict/
├── manage.py                    # Django管理コマンド
├── requirements.txt             # 依存パッケージ
├── snow_predict/               # プロジェクト設定
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── prediction/                 # 予測アプリ
│   ├── models.py              # データモデル
│   ├── views.py               # ビュー関数
│   ├── forms.py               # フォーム定義
│   ├── utils.py               # 予測ユーティリティ
│   ├── urls.py                # URLルーティング
│   ├── admin.py               # 管理画面設定
│   └── management/
│       └── commands/
│           └── setup_resorts.py  # 初期データ設定
├── templates/                  # HTMLテンプレート
│   ├── base.html
│   └── prediction/
│       └── index.html
├── static/                     # 静的ファイル
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── prediction.js
└── data/                       # 予測モデルとデータ
    ├── *.pkl                  # Prophetモデルファイル
    └── *.csv                  # 履歴データファイル
```

## 使用方法

1. ブラウザでアプリケーションにアクセス
2. スキー場を選択
3. 予測したい月（11月-4月）をチェックボックスで選択
4. 「予測を実行」ボタンをクリック
5. 結果として過去10シーズンとの比較グラフと予測データテーブルが表示

## 技術スタック

- **バックエンド**: Django 4.2+
- **フロントエンド**: HTML5, Bootstrap 5, JavaScript
- **グラフライブラリ**: Chart.js
- **機械学習**: Prophet (Facebook)
- **データ処理**: pandas, numpy
- **データベース**: SQLite（デフォルト）

## 注意事項

- Prophetライブラリは初回インストール時に時間がかかる場合があります
- 予測精度は過去のデータに基づいており、実際の気象条件により結果は変動する可能性があります
