from django.core.management.base import BaseCommand
from prediction.models import SkiResort


class Command(BaseCommand):
    help = 'スキー場のマスターデータを初期設定します'

    def handle(self, *args, **options):
        resorts_data = [
            {
                "name": "野沢温泉",
                "model_file": "data/nozawa_model.pkl",
                "csv_file": "data/nozawa_data.csv"
            },
            {
                "name": "湯沢",
                "model_file": "data/yuzawa_model.pkl",
                "csv_file": "data/Yuzawa_data.csv"
            },
            {
                "name": "白馬",
                "model_file": "data/hakuba_model.pkl",
                "csv_file": "data/Hakuba_data.csv"
            },
            {
                "name": "軽井沢",
                "model_file": "data/karuizawa_model.pkl",
                "csv_file": "data/Karuizawa_data.csv"
            },
            {
                "name": "菅平",
                "model_file": "data/sugadaira_model.pkl",
                "csv_file": "data/Sugadaira_data.csv"
            },
            {
                "name": "草津",
                "model_file": "data/kusatsu_model.pkl",
                "csv_file": "data/Kusatsu_data.csv"
            },
            {
                "name": "猪苗代",
                "model_file": "data/inawashiro_model.pkl",
                "csv_file": "data/Inawashiro_data.csv"
            }
        ]

        created_count = 0
        updated_count = 0

        for resort_data in resorts_data:
            resort, created = SkiResort.objects.get_or_create(
                name=resort_data["name"],
                defaults={
                    "model_file": resort_data["model_file"],
                    "csv_file": resort_data["csv_file"]
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'スキー場 "{resort.name}" を作成しました。')
                )
            else:
                # 既存データの更新
                resort.model_file = resort_data["model_file"]
                resort.csv_file = resort_data["csv_file"]
                resort.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'スキー場 "{resort.name}" を更新しました。')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'初期設定完了: {created_count}件作成, {updated_count}件更新'
            )
        )
