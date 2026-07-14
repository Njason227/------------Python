from django.contrib import admin
from .models import Patient, AssignmentLog


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'date_of_birth', 'status', 'department', 'admission_date')
    list_filter = ('status', 'gender', 'department')
    search_fields = ('last_name', 'first_name', 'patronymic')
    readonly_fields = ('admission_date', 'created_at', 'updated_at')


@admin.register(AssignmentLog)
class AssignmentLogAdmin(admin.ModelAdmin):
    list_display = ('patient', 'from_department', 'to_department', 'assigned_by', 'is_automatic', 'created_at')
    list_filter = ('is_automatic', 'to_department')
    readonly_fields = ('created_at',)
