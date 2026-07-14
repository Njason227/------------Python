from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('export/csv/', views.export_patients_csv, name='export_csv'),
]
