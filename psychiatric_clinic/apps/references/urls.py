from django.urls import path
from . import views

app_name = 'references'

urlpatterns = [
    path('', views.index_view, name='index'),

    path('gender/', views.gender_list_view, name='gender_list'),
    path('gender/create/', views.gender_create_view, name='gender_create'),
    path('gender/<int:pk>/edit/', views.gender_edit_view, name='gender_edit'),
    path('gender/<int:pk>/delete/', views.gender_delete_view, name='gender_delete'),

    path('mental-severity/', views.mental_severity_list_view, name='mental_severity_list'),
    path('mental-severity/create/', views.mental_severity_create_view, name='mental_severity_create'),
    path('mental-severity/<int:pk>/edit/', views.mental_severity_edit_view, name='mental_severity_edit'),
    path('mental-severity/<int:pk>/delete/', views.mental_severity_delete_view, name='mental_severity_delete'),

    path('physical-severity/', views.physical_severity_list_view, name='physical_severity_list'),
    path('physical-severity/create/', views.physical_severity_create_view, name='physical_severity_create'),
    path('physical-severity/<int:pk>/edit/', views.physical_severity_edit_view, name='physical_severity_edit'),
    path('physical-severity/<int:pk>/delete/', views.physical_severity_delete_view, name='physical_severity_delete'),

    path('diagnosis/', views.diagnosis_list_view, name='diagnosis_list'),
    path('diagnosis/create/', views.diagnosis_create_view, name='diagnosis_create'),
    path('diagnosis/<int:pk>/edit/', views.diagnosis_edit_view, name='diagnosis_edit'),
    path('diagnosis/<int:pk>/delete/', views.diagnosis_delete_view, name='diagnosis_delete'),

    path('departments/', views.department_list_view, name='department_list'),
    path('departments/create/', views.department_create_view, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit_view, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete_view, name='department_delete'),
]
