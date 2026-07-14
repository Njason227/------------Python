from django import forms
from .models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department


class GenderForm(forms.ModelForm):
    class Meta:
        model = Gender
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}


class MentalSeverityForm(forms.ModelForm):
    class Meta:
        model = MentalSeverity
        fields = ['name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 4}),
        }


class PhysicalSeverityForm(forms.ModelForm):
    class Meta:
        model = PhysicalSeverity
        fields = ['name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 4}),
        }


class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ['code', 'name', 'block', 'chapter', 'parent']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'block': forms.TextInput(attrs={'class': 'form-control'}),
            'chapter': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            'name', 'profile', 'profile_diagnoses',
            'gender_restriction', 'age_category',
            'total_beds', 'occupied_beds', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'profile_diagnoses': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 8}),
            'gender_restriction': forms.Select(attrs={'class': 'form-select'}),
            'age_category': forms.Select(attrs={'class': 'form-select'}),
            'total_beds': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'occupied_beds': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
