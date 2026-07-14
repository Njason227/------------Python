from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Patient
from .forms import PatientForm, PatientFilterForm


@login_required
def patient_list_view(request):
    form = PatientFilterForm(request.GET)
    patients = Patient.objects.select_related('gender', 'diagnosis', 'mental_severity', 'physical_severity', 'department')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            patients = patients.filter(
                Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(patronymic__icontains=q)
            )
        status = form.cleaned_data.get('status')
        if status:
            patients = patients.filter(status=status)
        gender = form.cleaned_data.get('gender')
        if gender:
            patients = patients.filter(gender=gender)
        age_cat = form.cleaned_data.get('age_category')
        if age_cat == 'child':
            from datetime import date, timedelta
            threshold = date.today() - timedelta(days=365*18)
            patients = patients.filter(date_of_birth__gt=threshold)
        elif age_cat == 'adult':
            from datetime import date, timedelta
            threshold = date.today() - timedelta(days=365*18)
            patients = patients.filter(date_of_birth__lte=threshold)

    paginator = Paginator(patients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'patients/patient_list.html', {
        'page_obj': page_obj,
        'filter_form': form,
    })


@login_required
def patient_create_view(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Пациент {patient.full_name} зарегистрирован.')
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientForm()
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Регистрация пациента'})


@login_required
def patient_detail_view(request, pk):
    patient = get_object_or_404(
        Patient.objects.select_related(
            'gender', 'diagnosis', 'mental_severity', 'physical_severity', 'department', 'assigned_by'
        ), pk=pk
    )
    logs = patient.assignment_logs.select_related('from_department', 'to_department', 'assigned_by')[:20]
    return render(request, 'patients/patient_detail.html', {'patient': patient, 'logs': logs})


@login_required
def patient_edit_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные пациента {patient.full_name} обновлены.')
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patients/patient_form.html', {
        'form': form, 'title': f'Редактирование: {patient.full_name}'
    })


@login_required
def patient_delete_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        name = patient.full_name
        patient.delete()
        messages.success(request, f'Пациент {name} удалён.')
        return redirect('patients:list')
    return render(request, 'patients/patient_confirm_delete.html', {'patient': patient})
