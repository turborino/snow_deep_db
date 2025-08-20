import streamlit as st
import pickle
import pandas as pd
from prophet.plot import plot_plotly
import os
import plotly.graph_objects as go

# --- 1. アプリの基本設定 ---

st.set_page_config(page_title="スキーリゾート積雪予測AI", layout="wide")
st.title('❄️ スキーリゾート積雪予測AI (月次版) ❄️')
st.write('AIが選択したスキーリゾートの未来の積雪量を月単位で予測します。')

# --- 2. モデルとデータファイルの管理 ---

# ★★★ あなたのファイル名に合わせて、この辞書を完成させてください ★★★
RESORT_DATA = {
    "野沢温泉": {
        "model": "nozawa_monthly_model.pkl",
        "csv": "data/nozawa_data.csv"
    },
    "湯沢": {
        "model": "yuzawa_monthly_model.pkl",
        "csv": "data/Yuzawa_data.csv"
    },
    # (ここに残りのリゾートの情報を追加してください)
}

# --- 3. 関数定義 ---

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

@st.cache_data
def load_csv_data(resort_name):
    """月次CSVデータを読み込み、前処理を行う"""
    file_path = RESORT_DATA[resort_name]["csv"]
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    df['ds'] = pd.to_datetime(df['年月'], format='%b-%y')
    feature_cols = ['平均気温(℃)', '降雪量合計(cm)'] # ★★★ あなたが分析で使った特徴量をリストにしてください ★★★
    df[feature_cols] = df[feature_cols].fillna(0)
    return df

@st.cache_resource
def load_model(resort_name):
    """月次モデルを読み込む"""
    file_path = RESORT_DATA[resort_name]["model"]
    if not os.path.exists(file_path): return None
    with open(file_path, 'rb') as f:
        model = pickle.load(f)
    return model

# --- 4. ユーザー操作部分（サイドバー） ---
st.sidebar.header('予測の設定')
selected_resort = st.sidebar.selectbox('スキー場を選択してください', list(RESORT_DATA.keys()))
months_to_predict = st.sidebar.number_input("何か月先まで予測しますか？", min_value=6, max_value=36, value=12, step=1)
execute_button = st.sidebar.button('予測を実行 →')

# --- 5. 予測と結果表示（メイン画面） ---
if execute_button:
    st.header(f'📍 {selected_resort} の予測結果')

    model = load_model(selected_resort)
    historical_df = load_csv_data(selected_resort)

    if model and historical_df is not None:
        with st.spinner('AIが予測を計算しています...'):
            future_df = model.make_future_dataframe(periods=months_to_predict, freq='MS')
            regressor_names = list(model.extra_regressors.keys())
            if regressor_names:
                historical_df['month'] = historical_df['ds'].dt.month
                seasonal_averages = historical_df.groupby('month')[regressor_names].mean().reset_index()
                future_df['month'] = future_df['ds'].dt.month
                future_df = pd.merge(future_df, seasonal_averages, on='month', how='left').drop(columns=['month'])
                future_df = future_df.fillna(method='ffill').fillna(method='bfill')
            forecast = model.predict(future_df)

        st.subheader('過去実績との比較グラフ')
        comparison_fig = create_comparison_bar_chart(forecast, historical_df.rename(columns={'y': 'value'}))
        st.plotly_chart(comparison_fig, use_container_width=True)

        with st.expander("詳細な時系列予測グラフを見る"):
            st.subheader('時系列予測グラフ全体')
            fig_prophet = plot_plotly(model, forecast)
            st.plotly_chart(fig_prophet, use_container_width=True)

        st.subheader('予測データ詳細')
        future_forecast_display = forecast[forecast['ds'] > historical_df['ds'].max()].copy()
        
        prediction_cols = ['yhat', 'yhat_lower', 'yhat_upper']
        for col in prediction_cols:
            future_forecast_display[col] = future_forecast_display[col].clip(lower=0)

        future_forecast_display['ds'] = future_forecast_display['ds'].dt.strftime('%Y-%m')
        
        st.dataframe(
            future_forecast_display[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(
                columns={'ds': '年月', 'yhat': '予測値(cm)', 'yhat_lower': '予測下限(cm)', 'yhat_upper': '予測上限(cm)'}
            ),
            hide_index=True
        )
    else:
        st.error(f'エラー: {selected_resort}のモデルまたはCSVファイルが見つかりません。')
else:
    st.info('サイドバーで設定を選んで「予測を実行」ボタンを押してください。')