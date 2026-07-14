from django.urls import path
from . import views

app_name = 'distribution'

urlpatterns = [
    path('queue/', views.queue_view, name='queue'),
    path('auto/<int:patient_id>/', views.auto_distribute_view, name='auto_distribute'),
    path('auto-check/<int:patient_id>/', views.auto_distribute_check_view, name='auto_distribute_check'),
    path('auto-all/', views.auto_distribute_all_view, name='auto_distribute_all'),
    path('manual/', views.manual_assign_view, name='manual_assign'),
    path('history/', views.history_view, name='history'),
    path('departments/', views.department_load_view, name='department_load'),
    path('rules/', views.rules_list_view, name='rules_list'),
    path('rules/<int:pk>/delete/', views.rule_delete_view, name='rule_delete'),
]
