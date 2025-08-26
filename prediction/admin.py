from django.contrib import admin
from .models import SkiResort, Prediction


@admin.register(SkiResort)
class SkiResortAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_file', 'csv_file', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('resort', 'created_at')
    list_filter = ('resort', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('resort__name',)
