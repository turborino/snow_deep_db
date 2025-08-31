import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from .forms import PredictionForm
from .models import SkiResort
from .utils import load_model, load_csv_data, create_prediction_data, create_comparison_data


def index(request):
    """メインページ"""
    form = PredictionForm()
    return render(request, 'prediction/index.html', {'form': form})


@require_http_methods(["POST"])
def predict(request):
    """予測実行"""
    form = PredictionForm(request.POST)
    
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    resort = form.cleaned_data['resort']
    selected_months = [int(month) for month in form.cleaned_data['months']]
    
    # モデルとデータを読み込み
    model = load_model(resort.model_file)
    historical_df = load_csv_data(resort.csv_file)
    
    if model is None or historical_df is None:
        return JsonResponse({
            'success': False,
            'error': f'{resort.name}のモデルまたはCSVファイルが見つかりません。'
        }, status=500)
    
    try:
        # 予測実行
        future_forecast, full_forecast, historical_df = create_prediction_data(
            model, historical_df, selected_months
        )
        
        # 予測データテーブル用の整形
        prediction_table = []
        for _, row in future_forecast.iterrows():
            prediction_table.append({
                'date': row['ds'].strftime('%Y-%m'),
                'predicted': round(row['yhat'], 1),
                'lower': round(row['yhat_lower'], 1),
                'upper': round(row['yhat_upper'], 1)
            })
        
        # 比較グラフ用データ
        chart_data = create_comparison_data(full_forecast, historical_df, selected_months)
        
        return JsonResponse({
            'success': True,
            'resort_name': resort.name,
            'prediction_table': prediction_table,
            'chart_data': chart_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'予測計算中にエラーが発生しました: {str(e)}'
        }, status=500)


def health_check(request):
    """ALB ヘルスチェック用エンドポイント"""
    try:
        # データベース接続確認
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # スキー場データ確認
        resort_count = SkiResort.objects.count()
        
        return HttpResponse(
            f"OK - DB Connected, {resort_count} resorts available",
            status=200,
            content_type="text/plain"
        )
    except Exception as e:
        return HttpResponse(
            f"ERROR - {str(e)}",
            status=503,
            content_type="text/plain"
        )
