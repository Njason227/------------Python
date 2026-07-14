from django.contrib import admin
from .models import DistributionRule


@admin.register(DistributionRule)
class DistributionRuleAdmin(admin.ModelAdmin):
    list_display = ('department', 'diagnosis', 'gender', 'age_category', 'priority', 'is_active')
    list_filter = ('is_active', 'priority', 'department')
    list_editable = ('is_active',)
