from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q
from datetime import date, timedelta
import csv

from apps.patients.models import Patient
from apps.references.models import Department, Gender, MentalSeverity, PhysicalSeverity


def home_redirect(request):
    if request.user.is_authenticated:
        return render(request, 'home.html')
    return render(request, 'home.html')


@login_required
def dashboard_view(request):
    total_patients = Patient.objects.count()
    waiting = Patient.objects.filter(status='waiting').count()
    assigned = Patient.objects.filter(status='assigned').count()
    hospitalized = Patient.objects.filter(status='hospitalized').count()

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    admissions_today = Patient.objects.filter(admission_date__date=today).count()
    admissions_week = Patient.objects.filter(admission_date__date__gte=week_ago).count()
    admissions_month = Patient.objects.filter(admission_date__date__gte=month_ago).count()

    departments = Department.objects.filter(is_active=True).order_by('name')
    dept_stats = []
    for dept in departments:
        dept_stats.append({
            'department': dept,
            'total_beds': dept.total_beds,
            'occupied_beds': dept.occupied_beds,
            'available_beds': dept.available_beds,
            'occupancy_percent': dept.occupancy_percent,
        })

    gender_stats = Patient.objects.values('gender__name').annotate(count=Count('id')).order_by('gender__name')

    age_child = Patient.objects.filter(
        date_of_birth__gt=today - timedelta(days=365*18)
    ).count()
    age_adult = total_patients - age_child

    mental_stats = Patient.objects.values('mental_severity__name', 'mental_severity__level').annotate(
        count=Count('id')
    ).order_by('mental_severity__level')

    physical_stats = Patient.objects.values('physical_severity__name', 'physical_severity__level').annotate(
        count=Count('id')
    ).order_by('physical_severity__level')

    context = {
        'total_patients': total_patients,
        'waiting': waiting,
        'assigned': assigned,
        'hospitalized': hospitalized,
        'admissions_today': admissions_today,
        'admissions_week': admissions_week,
        'admissions_month': admissions_month,
        'dept_stats': dept_stats,
        'gender_stats': gender_stats,
        'age_child': age_child,
        'age_adult': age_adult,
        'mental_stats': mental_stats,
        'physical_stats': physical_stats,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def export_patients_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="patients.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ФИО', 'Дата рождения', 'Возраст', 'Пол', 'Диагноз (МКБ-11)',
        'Тяжесть псих.', 'Тяжесть физ.', 'Статус', 'Отделение',
        'Дата поступления', 'Врач'
    ])

    patients = Patient.objects.select_related(
        'gender', 'diagnosis', 'mental_severity', 'physical_severity',
        'department', 'assigned_by'
    ).order_by('-admission_date')

    for p in patients:
        writer.writerow([
            p.full_name,
            p.date_of_birth,
            p.age,
            p.gender.name,
            str(p.diagnosis),
            p.mental_severity.name,
            p.physical_severity.name,
            p.get_status_display(),
            p.department.name if p.department else '',
            p.admission_date.strftime('%d.%m.%Y %H:%M'),
            p.assigned_by.get_full_name() if p.assigned_by else '',
        ])

    return response
