from django.contrib import admin
from .models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(MentalSeverity)
class MentalSeverityAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')


@admin.register(PhysicalSeverity)
class PhysicalSeverityAdmin(admin.ModelAdmin):
    list_display = ('name', 'level')


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'block', 'chapter')
    list_filter = ('chapter',)
    search_fields = ('code', 'name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender_restriction', 'age_category', 'total_beds', 'occupied_beds', 'is_active')
    list_filter = ('is_active', 'gender_restriction', 'age_category')
    filter_horizontal = ('profile_diagnoses',)
