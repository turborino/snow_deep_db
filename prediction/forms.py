from django import forms
from .models import SkiResort

MONTH_CHOICES = [
    (11, '11月'),
    (12, '12月'),
    (1, '1月'),
    (2, '2月'),
    (3, '3月'),
    (4, '4月'),
]


class PredictionForm(forms.Form):
    resort = forms.ModelChoiceField(
        queryset=SkiResort.objects.all(),
        empty_label="スキー場を選択してください",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg mb-3',
            'required': True
        }),
        label="スキー場"
    )
    
    months = forms.MultipleChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="予測したい月を選択",
        required=True,
        initial=[11, 12, 1, 2, 3, 4]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # デフォルトで全ての月を選択
        if not self.data:
            self.fields['months'].initial = [11, 12, 1, 2, 3, 4]
