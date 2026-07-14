from django import forms
from apps.references.models import Department
from apps.patients.models import Patient


class ManualAssignmentForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.filter(status='waiting'),
        label='Пациент',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        label='Отделение',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        required=False,
        label='Причина назначения',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        if department and department.available_beds <= 0:
            raise forms.ValidationError('В выбранном отделении нет свободных коек.')
        return cleaned_data


class DistributionRuleForm(forms.Form):
    from apps.references.models import Diagnosis
    from apps.distribution.models import DistributionRule

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        label='Отделение',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    diagnosis = forms.ModelChoiceField(
        required=False, queryset=Diagnosis.objects.all(),
        label='Диагноз (МКБ-11)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Любой'), ('M', 'Мужской'), ('F', 'Женский')],
        label='Пол',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    age_category = forms.ChoiceField(
        required=False,
        choices=[('', 'Любой'), ('CHILD', 'До 18 лет'), ('ADULT', '18+')],
        label='Возрастная категория',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_mental_severity = forms.IntegerField(
        min_value=1, max_value=4, initial=1,
        label='Мин. псих. тяжесть',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    max_mental_severity = forms.IntegerField(
        min_value=1, max_value=4, initial=4,
        label='Макс. псих. тяжесть',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    min_physical_severity = forms.IntegerField(
        min_value=1, max_value=4, initial=1,
        label='Мин. физ. тяжесть',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    max_physical_severity = forms.IntegerField(
        min_value=1, max_value=4, initial=4,
        label='Макс. физ. тяжесть',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=DistributionRule.PRIORITY_CHOICES,
        initial=3,
        label='Приоритет',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
