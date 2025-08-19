import streamlit as st
import pickle
import pandas as pd
from prophet.plot import plot_plotly
import os
import plotly.graph_objects as go # グラフ作成ライブラリをインポート

# --- 1. 事前準備 ---

st.set_page_config(page_title="スキーリゾート積雪予測AI", layout="wide")
st.title('❄️ スキーリゾート積雪予測AI ❄️')
st.write('AIが選択したスキーリゾートの未来の積雪量を予測します。')

# --- モデルとデータの準備 ---

# 各リゾートのモデルとCSVデータのパスを管理する土台です。
# ★★★ ファイル名に合わせて、この設定を変更します ★★★
RESORT_DATA = {
    "野沢": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/nozawa_data.csv" # データセットはココに（追加するときには変数にて行う予定）
    },
    "白馬": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/Hakuba_data.csv"
    },
    "湯沢": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/Yuzawa_data.csv"
	},
    "草津": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/Kusatsu_data.csv"
    },
    "軽井沢": {
        "model": "data/karuizawa_model.pkl",
        "csv": "data/Karuizawa_data.csv"
    },
    "猪苗代": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/Inawashiro_data.csv"
    },
    "菅平": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/Sugadaira_data.csv"
    },
    # (追加する場合はここに情報を追加します)
}

# --- 関数定義 ---

# ▼▼▼ シーズンのバーグラフをを作成する関数 ▼▼▼
def create_comparison_bar_chart(forecast, historical_df):
    """過去10シーズンと未来予測を比較する棒グラフを作成する"""
    
    # データを結合し、シーズン情報を付加します
    df = pd.concat([
        historical_df.rename(columns={'y': 'value'}), # 過去データ
        forecast[forecast['ds'] > historical_df['ds'].max()].rename(columns={'yhat': 'value'}) # 未来データ
    ])
    df['ds'] = pd.to_datetime(df['ds'])

    # スキーシーズンの定義（11月から翌年4月）に絞ります。
    winter_months = [11, 12, 1, 2, 3, 4]
    df = df[df['ds'].dt.month.isin(winter_months)]

    # シーズンを定義する関数 (2025年11月 -> 2025-26シーズン)
    def get_season(date):
        if date.month >= 11:
            return f"{date.year}-{date.year + 1}"
        else:
            return f"{date.year - 1}-{date.year}"
    df['season'] = df['ds'].apply(get_season)

    # 直近10シーズンと未来の1シーズンに絞り込み
    all_seasons = sorted(df['season'].unique())
    target_seasons = all_seasons[-11:] 
    df = df[df['season'].isin(target_seasons)]

    # 月とシーズンでピボットテーブルを作成
    # pivot_tableで使うために、月の列を明示して作成
    df['month'] = df['ds'].dt.month
    pivot_df = df.pivot_table(index='month', columns='season', values='value')
 

    pivot_df = pivot_df.reindex(winter_months) # 月の並び順を固定します
    
    # グラフの作成
    fig = go.Figure()
    month_labels = {11: '11月', 12: '12月', 1: '1月', 2: '2月', 3: '3月', 4: '4月'}
    
    for season in pivot_df.columns:
        # 未来の予測シーズンは色を変える
        is_future = pivot_df[season].isnull().sum() < len(pivot_df)
        
        fig.add_trace(go.Bar(
            x=[month_labels.get(i) for i in pivot_df.index],
            y=pivot_df[season],
            name=season,
            marker_color='crimson' if is_future else 'cornflowerblue',
            opacity=1.0 if is_future else 0.6
        ))

    fig.update_layout(
        title='<b>過去10シーズンと未来予測の月別積雪量比較</b>',
        xaxis_title='月',
        yaxis_title='積雪量 (cm)',
        legend_title='シーズン',
        barmode='group', # グループ化された棒グラフ
        plot_bgcolor='white'
    )
    return fig

# @st.cache_data はデータの読み込みを高速化するおまじない
@st.cache_data
def load_csv_data(resort_name):
    """月次CSVデータを読み込む"""
    file_path = RESORT_DATA[resort_name]["csv"]
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Prophetが日付として認識できるように変換します。
        df['ds'] = pd.to_datetime(df['年月'], format='%b-%y')
        feature_cols = ['日最高気温の平均(℃)', '降雪量日合計3cm以上日数(日)','日最低気温0℃未満日数(日)']
        df[feature_cols] = df[feature_cols].fillna(0)
        return df
    else:
        return None

# @st.cache_resource はモデルの読み込みを高速化するおまじない
@st.cache_resource
def load_model(resort_name):
    """月次モデルを読み込む"""
    file_path = RESORT_DATA[resort_name]["model"]
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            model = pickle.load(f)
        return model
    else:
        return None

# --- 2. ユーザー操作部分（サイドバー） ---

st.sidebar.header('予測の設定')
selected_resort = st.sidebar.selectbox(
    'スキー場を選択してください',
    list(RESORT_DATA.keys())
)
# 予測する月数をユーザーが入力
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

    if model and historical_df is not None:
        with st.spinner('AIが予測を計算しています...'):
            # 1. 未来の「月初の日付」リストを作成します
            future_df = model.make_future_dataframe(
                periods=months_to_predict, freq='MS'
            )

            # 2. 未来の「天気」（特徴量）を推測してfuture_dfに結合します
            regressor_names = list(model.extra_regressors.keys())
            if regressor_names:
                historical_df['month'] = historical_df['ds'].dt.month
                seasonal_averages = historical_df.groupby('month')[regressor_names].mean().reset_index()

                future_df['month'] = future_df['ds'].dt.month
                future_df = pd.merge(future_df, seasonal_averages, on='month', how='left')
                future_df = future_df.drop(columns=['month'])
                
                # 前方と後方の両方から値を埋めて、NaNが残らないようにします
                future_df = future_df.fillna(method='ffill').fillna(method='bfill')

            # 3. 特徴量が入ったfuture_dfで予測を実行します
            forecast = model.predict(future_df)

        st.subheader('過去実績との比較グラフ')
        # 新しい関数を呼び出して比較棒グラフを作成・表示させます
        comparison_fig = create_comparison_bar_chart(forecast, historical_df.rename(columns={'y': 'value'}))
        st.plotly_chart(comparison_fig, use_container_width=True)
        # ▲▲▲ 変更点ここまで ▲▲▲

        # 念のため、元のProphetの予測グラフも残しておきます（折りたたみ表示）
        with st.expander("詳細な時系列予測グラフを見る"):
            st.subheader('時系列予測グラフ全体')
            fig_prophet = plot_plotly(model, forecast)
            st.plotly_chart(fig_prophet, use_container_width=True)

        st.subheader('予測データ詳細')
        future_forecast = forecast[forecast['ds'] > historical_df['ds'].max()]
        st.dataframe(future_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(
            columns={'ds': '日付', 'yhat': '予測値(cm)', 'yhat_lower': '予測下限(cm)', 'yhat_upper': '予測上限(cm)'}
        ))
    else:
        st.error(f'エラー: {selected_resort}のモデルまたはCSVファイルが見つかりません。')
else:
    st.info('サイドバーで設定を選んで「予測を実行」ボタンを押してください。')
