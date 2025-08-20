import streamlit as st
import pickle
import pandas as pd
from prophet.plot import plot_plotly
import os
import plotly.graph_objects as go

st.set_page_config(page_title="スキーリゾート積雪予測AI", layout="wide")
st.title('❄️ スキーリゾート積雪予測AI (月次版) ❄️')
st.write('AIが選択したスキーリゾートの未来の積雪量を月単位で予測します。')

RESORT_DATA = {
    "野沢温泉": {
        "model": "data/nozawa_model.pkl",
        "csv": "data/nozawa_data.csv"
    },
    "湯沢": {
        "model": "data/yuzawa_model.pkl",
        "csv": "data/Yuzawa_data.csv"
    },
    "白馬": {
        "model": "data/hakuba_model.pkl",
        "csv": "data/Hakuba_data.csv"
    },
    "軽井沢": {
        "model": "data/karuizawa_model.pkl",
        "csv": "data/Karuizawa_data.csv"
    },
    "菅平": {
        "model": "data/sugadaira_model.pkl",
        "csv": "data/Sugadaira_data.csv"
    },
    "草津": {
        "model": "data/kusatsu_model.pkl",
        "csv": "data/Kusatsu_data.csv"
    },
    "猪苗代": {
        "model": "data/inawashiro_model.pkl",
        "csv": "data/Inawashiro_data.csv"
    },

}

def create_comparison_bar_chart(forecast, historical_df):
    forecast_clipped = forecast.copy()
    forecast_clipped['yhat'] = forecast_clipped['yhat'].clip(lower=0)

    df = pd.concat([
        historical_df.rename(columns={'y': 'value'}),
        forecast_clipped[forecast_clipped['ds'] > historical_df['ds'].max()].rename(columns={'yhat': 'value'})
    ])
    df['ds'] = pd.to_datetime(df['ds'])

    winter_months = [11, 12, 1, 2, 3, 4]
    df = df[df['ds'].dt.month.isin(winter_months)]

    def get_season(date):
        if date.month >= 11:
            return f"{date.year}-{date.year + 1}"
        else:
            return f"{date.year - 1}-{date.year}"
    df['season'] = df['ds'].apply(get_season)

    all_seasons = sorted(df['season'].unique())
    target_seasons = all_seasons[-11:] 
    df = df[df['season'].isin(target_seasons)]

    pivot_df = df.pivot_table(index=df['ds'].dt.month, columns='season', values='value')
    pivot_df = pivot_df.reindex(winter_months)
    
    fig = go.Figure()
    month_labels = {11: '11月', 12: '12月', 1: '1月', 2: '2月', 3: '3月', 4: '4月'}
    
    future_season_name = pivot_df.columns[-1]

    for season in pivot_df.columns:
        is_future = (season == future_season_name)
        
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
        barmode='group',
        plot_bgcolor='white'
    )
    return fig

@st.cache_data
def load_csv_data(resort_name):
    file_path = RESORT_DATA[resort_name]["csv"]
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    df['ds'] = pd.to_datetime(df['年月'], format='%b-%y')
    feature_cols = ['平均気温(℃)', '降雪量合計(cm)']
    df[feature_cols] = df[feature_cols].fillna(0)
    return df

@st.cache_resource
def load_model(resort_name):
    file_path = RESORT_DATA[resort_name]["model"]
    if not os.path.exists(file_path): return None
    with open(file_path, 'rb') as f:
        model = pickle.load(f)
    return model

st.sidebar.header('予測の設定')
selected_resort = st.sidebar.selectbox('スキー場を選択してください', list(RESORT_DATA.keys()))
months_to_predict = st.sidebar.number_input("何か月先まで予測しますか？", min_value=6, max_value=36, value=12, step=1)
execute_button = st.sidebar.button('予測を実行 →')

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