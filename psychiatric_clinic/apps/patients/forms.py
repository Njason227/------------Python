from django import forms
from .models import Patient
from apps.references.models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'last_name', 'first_name', 'patronymic', 'date_of_birth',
            'gender', 'diagnosis', 'mental_severity', 'physical_severity',
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'diagnosis': forms.Select(attrs={'class': 'form-select'}),
            'mental_severity': forms.Select(attrs={'class': 'form-select'}),
            'physical_severity': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['last_name'].label = 'Фамилия'
        self.fields['first_name'].label = 'Имя'
        self.fields['patronymic'].label = 'Отчество'
        self.fields['date_of_birth'].label = 'Дата рождения'
        self.fields['gender'].label = 'Пол'
        self.fields['diagnosis'].label = 'Диагноз (МКБ-11)'
        self.fields['mental_severity'].label = 'Тяжесть психического состояния'
        self.fields['physical_severity'].label = 'Тяжесть физического состояния'

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > forms.DateField().clean(str(dob)):
            from datetime import date
            if dob > date.today():
                raise forms.ValidationError('Дата рождения не может быть в будущем.')
        return dob


class PatientFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Поиск по ФИО',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО...'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Все')] + Patient.STATUS_CHOICES,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    gender = forms.ModelChoiceField(
        required=False,
        queryset=Gender.objects.all(),
        label='Пол',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все'
    )
    age_category = forms.ChoiceField(
        required=False,
        choices=[('', 'Все'), ('child', 'До 18 лет'), ('adult', '18 лет и старше')],
        label='Возрастная категория',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
