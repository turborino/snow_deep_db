import streamlit as st
import pickle
import pandas as pd
from prophet.plot import plot_plotly
import os
import plotly.graph_objects as go # グラフ作成ライブラリをインポート

# --- 1. 事前準備 ---
# ブラウザのタブに表示されるタイトルと、ページのレイアウトを設定します
st.set_page_config(page_title="スキーリゾート積雪予測AI", layout="wide")
# アプリのメインタイトルを表示
st.title('❄️ スキーリゾート積雪予測AI ❄️')
# アプリの簡単な説明を表示します
st.write('AIが選択したスキーリゾートの未来の積雪量を予測します。')

# --- モデルとデータの準備 ---
# ここに、「学習済モデル」と「CSVデータファイル」の場所を登録します。
# このアプリの根幹部分ですね。
RESORT_DATA = {
    "野沢": {
        "model": "data/nozawa_model.pkl", # 学習済モデルの呼び出し
        "csv": "data/nozawa_data.csv" # 分析に使った月次データ
    },
    "草津": {
        "model": "data/kusatsu_model.pkl",
        "csv": "data/Kusatsu_data.csv"
    },
    "白馬": {
        "model": "data/hakuba_model.pkl",
        "csv": "data/Hakuba_data.csv"        
    },
    "湯沢": {
        "model": "data/yuzawa_model.pkl",
        "csv": "data/Yuzawa_data.csv"
    },
  
    "軽井沢": {
        "model": "data/karuizawa_model.pkl",
        "csv": "data/Karuizawa_data.csv"
    },
    "猪苗代": {
        "model": "data/inawashiro_model.pkl",
        "csv": "data/Inawashiro_data.csv"
    },
    "菅平": {
        "model": "data/sugadaira_model.pkl",
        "csv": "data/Sugadaira_data.csv"
    },
    # (追加する場合はここに情報を追加します)
}


# --- 関数定義 ---

# ▼▼▼　以下は比較棒グラフを作成する関数になります ▼▼▼
def create_comparison_bar_chart(forecast, historical_df):
    """過去10シーズンと未来予測を比較する棒グラフを作成する"""
    
    # 予測値(yhat)のマイナス値を0に丸める
    forecast_clipped = forecast.copy()
    forecast_clipped['yhat'] = forecast_clipped['yhat'].clip(lower=0)

    # 過去データと、0に丸めた「未来予測データ」を結合
    df = pd.concat([
        historical_df.rename(columns={'y': 'value'}),
        forecast_clipped[forecast_clipped['ds'] > historical_df['ds'].max()].rename(columns={'yhat': 'value'})
    ])
    df['ds'] = pd.to_datetime(df['ds'])

    # スキーシーズンとして比較したい月を定義
    winter_months = [11, 12, 1, 2, 3, 4]
    df = df[df['ds'].dt.month.isin(winter_months)]

    # 日付から「シーズン」(例: '2023-2024')を判定する関数
    def get_season(date):
        if date.month >= 11:
            return f"{date.year}-{date.year + 1}"
        else:
            return f"{date.year - 1}-{date.year}"
    df['season'] = df['ds'].apply(get_season)

    # 比較対象とするシーズンを、直近10シーズンと未来の1シーズンに絞り込む
    all_seasons = sorted(df['season'].unique())
    target_seasons = all_seasons[-11:] 
    df = df[df['season'].isin(target_seasons)]

    # グラフ作成のためにデータをピボット
    pivot_df = df.pivot_table(index=df['ds'].dt.month, columns='season', values='value')
    pivot_df = pivot_df.reindex(winter_months) # 月の並び順を固定
    
    # グラフの作成
    fig = go.Figure()
    month_labels = {11: '11月', 12: '12月', 1: '1月', 2: '2月', 3: '3月', 4: '4月'}
    
    # 未来の予測シーズン名を取得（最も新しいシーズン名）
    future_season_name = pivot_df.columns[-1]

    # シーズンごとに棒グラフを追加していく
    for season in pivot_df.columns:
        # 未来の予測シーズンかどうかを判定
        is_future = (season == future_season_name)
        
        fig.add_trace(go.Bar(
            x=[month_labels.get(i) for i in pivot_df.index],
            y=pivot_df[season],
            name=season,
            marker_color='crimson' if is_future else 'cornflowerblue', # 未来なら赤、過去なら青
            opacity=1.0 if is_future else 0.6 # 未来を濃く、過去を少し薄く
        ))

    # グラフ全体のデザインを調整
    fig.update_layout(
        title='<b>過去10シーズンと未来予測の月別積雪量比較</b>',
        xaxis_title='月',
        yaxis_title='積雪量 (cm)',
        legend_title='シーズン',
        barmode='group',
        plot_bgcolor='white'
    )
    return fig

# @st.cache_data はデータの読み込みを高速化する呪文（キャッシュ化）
@st.cache_data
def load_csv_data(resort_name):
    """月次CSVデータを読み込む"""
    file_path = RESORT_DATA[resort_name]["csv"]
    if os.path.exists(file_path):return None
    df = pd.read_csv(file_path)
    
    # Prophetが日付として認識できるように変換します（お決まりですね）

    df['ds'] = pd.to_datetime(df['年月'], format='%b-%y')
    feature_cols = ['日最高気温の平均(℃)', '降雪量日合計3cm以上日数(日)','日最低気温0℃未満日数(日)']
    df[feature_cols] = df[feature_cols].fillna(0)
    return df


# @st.cache_resource はモデルの読み込みを高速化する呪文（キャッシュ化）
@st.cache_resource
def load_model(resort_name):
    """月次モデルを読み込む"""
    file_path = RESORT_DATA[resort_name]["model"]
    if not os.path.exists(file_path): return None
    with open(file_path, 'rb') as f:
        model = pickle.load(f)
    return model

# --- 2. ユーザー操作部分（サイドバー） ---

st.sidebar.header('予測の設定')
selected_resort = st.sidebar.selectbox(
    'スキー場を選択してください',
    list(RESORT_DATA.keys())
)
# 予測する月数をユーザーが入力する欄
months_to_predict = st.sidebar.number_input(
    "何か月先まで予測しますか？",
    min_value=6, max_value=36, value=12, step=1
)

execute_button = st.sidebar.button('予測を実行 →')

# --- 3. 予測と結果表示（メイン画面） ---
if execute_button:
    st.header(f'📍 {selected_resort} の予測結果')

    model = load_model(selected_resort)
    historical_df = load_csv_data(selected_resort)
	
    # モデルとデータの両方が正常に読み込めた場合のみ、予測処理に進みます
    if model and historical_df is not None:
		
		# 処理中にスピナー（くるくる回るアイコン）を表示して、ユーザーに待機中であることを示します
        with st.spinner('AIが予測を計算しています...'):
            future_df = model.make_future_dataframe(periods=months_to_predict, freq='MS')
			# 未来の「天気」（追加特徴量）を推測してfuture_dfに結合する
            regressor_names = list(model.extra_regressors.keys())
            if regressor_names:
                historical_df['month'] = historical_df['ds'].dt.month
                seasonal_averages = historical_df.groupby('month')[regressor_names].mean().reset_index()
                future_df['month'] = future_df['ds'].dt.month
                future_df = pd.merge(future_df, seasonal_averages, on='month', how='left').drop(columns=['month'])
				# 前方(ffill)と後方(bfill)の両方から値を埋めて、NaN(欠損)が残らないようにします
                future_df = future_df.fillna(method='ffill').fillna(method='bfill')
			# 準備が整ったデータで、未来を予測します！
            forecast = model.predict(future_df)
		# 予測結果をグラフで表示します
        st.subheader('過去実績との比較グラフ')
        comparison_fig = create_comparison_bar_chart(forecast, historical_df.rename(columns={'y': 'value'}))
        st.plotly_chart(comparison_fig, use_container_width=True)
		
		# 参考として、Prophetが生成する元の時系列グラフも折りたたみメニューの中に表示させます
        with st.expander("詳細な時系列予測グラフを見る"):
            st.subheader('時系列予測グラフ全体')
            fig_prophet = plot_plotly(model, forecast)
            st.plotly_chart(fig_prophet, use_container_width=True)
		# 予測結果の元データをテーブル形式で表示させます
        st.subheader('予測データ詳細')
        # 表示用のデータフレームを準備します。
        future_forecast_display = forecast[forecast['ds'] > historical_df['ds'].max()].copy()
        
        # 予測値(yhat, yhat_lower, yhat_upper)がマイナスの場合、0に丸めます
        prediction_cols = ['yhat', 'yhat_lower', 'yhat_upper']
        for col in prediction_cols:
            future_forecast_display[col] = future_forecast_display[col].clip(lower=0)

        # 'ds'列（日付）の表示形式を 'YYYY-MM' (例: 2025-08) の文字列に変換して表示させます
        future_forecast_display['ds'] = future_forecast_display['ds'].dt.strftime('%Y-%m')
        
        # 整形したデータの、行番号を非表示にして表示させます
        st.dataframe(
            future_forecast_display[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(
                columns={'ds': '年月', 'yhat': '予測値(cm)', 'yhat_lower': '予測下限(cm)', 'yhat_upper': '予測上限(cm)'}
            ),
            hide_index=True # ★★★ 行番号を非表示にする設定 ★★★
        )
    else:
		# ファイルが見つからない場合のエラー表示です
        st.error(f'エラー: {selected_resort}のモデルまたはCSVファイルが見つかりません。')
else:
	# アプリの初期画面に表示されるメッセージです
    st.info('サイドバーで設定を選んで「予測を実行」ボタンを押してください。')
