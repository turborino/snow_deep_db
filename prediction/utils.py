import pickle
import pandas as pd
import os
from django.conf import settings


def load_model(model_path):
    """Prophet モデルを読み込む"""
    full_path = os.path.join(settings.BASE_DIR, model_path)
    if not os.path.exists(full_path):
        return None
    
    with open(full_path, 'rb') as f:
        model = pickle.load(f)
    return model


def load_csv_data(csv_path):
    """CSVデータを読み込む"""
    full_path = os.path.join(settings.BASE_DIR, csv_path)
    if not os.path.exists(full_path):
        return None
    
    df = pd.read_csv(full_path)
    df['ds'] = pd.to_datetime(df['年月'], format='%b-%y')
    df = df.rename(columns={'最深積雪(cm)': 'y'})
    
    feature_cols = ['日最高気温の平均(℃)', '降雪量日合計3cm以上日数(日)', '日最高気温0℃未満日数(日)']
    df[feature_cols] = df[feature_cols].fillna(0)
    return df


def create_prediction_data(model, historical_df, selected_months):
    """予測データを生成"""
    # 12ヶ月先まで予測
    future_df = model.make_future_dataframe(periods=12, freq='MS')
    
    # リグレッサーが存在する場合の処理
    regressor_names = list(model.extra_regressors.keys())
    if regressor_names:
        historical_df['month'] = historical_df['ds'].dt.month
        seasonal_averages = historical_df.groupby('month')[regressor_names].mean().reset_index()
        future_df['month'] = future_df['ds'].dt.month
        future_df = pd.merge(future_df, seasonal_averages, on='month', how='left').drop(columns=['month'])
        future_df = future_df.ffill().bfill()
    
    # 予測実行
    forecast = model.predict(future_df)
    
    # 未来の予測データのみ抽出
    future_forecast = forecast[forecast['ds'] > historical_df['ds'].max()].copy()
    
    # 負の値をクリップ
    prediction_cols = ['yhat', 'yhat_lower', 'yhat_upper']
    for col in prediction_cols:
        future_forecast[col] = future_forecast[col].clip(lower=0)
    
    # 選択された月のみフィルタ
    future_forecast = future_forecast[future_forecast['ds'].dt.month.isin(selected_months)]
    
    return future_forecast, forecast, historical_df


def create_comparison_data(forecast, historical_df, selected_months):
    """比較グラフ用のデータを作成"""
    historical_clipped = historical_df.copy()
    historical_clipped['value'] = historical_clipped['y'].clip(lower=0)
    
    forecast_clipped = forecast.copy()
    forecast_clipped['yhat'] = forecast_clipped['yhat'].clip(lower=0)

    # 履歴データと予測データを結合
    df = pd.concat([
        historical_clipped[['ds', 'value']],
        forecast_clipped[forecast_clipped['ds'] > historical_clipped['ds'].max()][['ds', 'yhat']].rename(columns={'yhat': 'value'})
    ])
    df['ds'] = pd.to_datetime(df['ds'])

    # 選択された月のみフィルタ
    df = df[df['ds'].dt.month.isin(selected_months)]

    # シーズン分け（11月-4月）
    def get_season(date):
        if date.month >= 11:
            return f"{date.year}-{date.year + 1}"
        else:
            return f"{date.year - 1}-{date.year}"
    
    df['season'] = df['ds'].apply(get_season)

    # 過去10シーズン + 未来1シーズン
    all_seasons = sorted(df['season'].unique())
    target_seasons = all_seasons[-11:]
    df = df[df['season'].isin(target_seasons)]

    # 月別にピボット
    pivot_df = df.pivot_table(index=df['ds'].dt.month, columns='season', values='value')
    pivot_df = pivot_df.reindex(selected_months)
    
    # Chart.js用にデータを整形
    month_labels = {11: '11月', 12: '12月', 1: '1月', 2: '2月', 3: '3月', 4: '4月'}
    
    chart_data = {
        'labels': [month_labels.get(month, str(month)) for month in pivot_df.index],
        'datasets': []
    }
    
    future_season = pivot_df.columns[-1] if len(pivot_df.columns) > 0 else None
    
    # シーズンを逆順に並べ替え（予測値が先頭、古い年が後）
    seasons_reversed = list(reversed(pivot_df.columns))
    
    for season in seasons_reversed:
        is_future = (season == future_season)
        
        chart_data['datasets'].append({
            'label': season,
            'data': [float(val) if pd.notna(val) else 0 for val in pivot_df[season]],
            'backgroundColor': 'rgba(220, 20, 60, 0.8)' if is_future else 'rgba(100, 149, 237, 0.6)',
            'borderColor': 'rgba(220, 20, 60, 1)' if is_future else 'rgba(100, 149, 237, 1)',
            'borderWidth': 2
        })
    
    return chart_data
