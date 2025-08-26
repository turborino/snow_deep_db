from django.db import models


class SkiResort(models.Model):
    """スキー場のマスターデータ"""
    name = models.CharField(max_length=100, unique=True, verbose_name="スキー場名")
    model_file = models.CharField(max_length=255, verbose_name="モデルファイルパス")
    csv_file = models.CharField(max_length=255, verbose_name="CSVファイルパス")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "スキー場"
        verbose_name_plural = "スキー場一覧"

    def __str__(self):
        return self.name


class Prediction(models.Model):
    """予測結果のログ"""
    resort = models.ForeignKey(SkiResort, on_delete=models.CASCADE, verbose_name="スキー場")
    selected_months = models.JSONField(verbose_name="選択された月")
    prediction_data = models.JSONField(verbose_name="予測データ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "予測結果"
        verbose_name_plural = "予測結果一覧"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.resort.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
