from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from apps.patients.models import Patient, AssignmentLog
from apps.references.models import Department
from .models import DistributionRule
from .forms import ManualAssignmentForm
from .services import DistributionService


@login_required
def queue_view(request):
    queue = DistributionService.get_queue()
    paginator = Paginator(queue, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'distribution/queue.html', {'page_obj': page_obj})


@login_required
def auto_distribute_check_view(request, patient_id):
    """API: проверка возможности автоматического распределения. Возвращает JSON."""
    patient = get_object_or_404(Patient, pk=patient_id)

    if patient.status != 'waiting':
        return JsonResponse({'status': 'error', 'message': 'Пациент уже распределён.'})

    dept, reasons = DistributionService.find_best_department(patient)

    if dept is None:
        return JsonResponse({
            'status': 'not_found',
            'message': 'Не удалось найти подходящее отделение.',
            'reasons': reasons,
        })

    if dept.available_beds <= 0:
        return JsonResponse({
            'status': 'full',
            'message': f'В отделении «{dept.name}» нет свободных мест. Желаете распределить вручную?',
            'department_id': dept.pk,
            'department_name': dept.name,
            'patient_id': patient.pk,
            'patient_name': patient.full_name,
            'reasons': reasons,
        })

    success, message = DistributionService.assign_patient(
        patient, dept, request.user,
        reason='\n'.join(reasons),
        is_automatic=True
    )

    if success:
        return JsonResponse({
            'status': 'assigned',
            'message': message,
            'department_name': dept.name,
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': message,
        })


@login_required
def auto_distribute_view(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)

    if patient.status != 'waiting':
        messages.warning(request, 'Пациент уже распределён или имеет другой статус.')
        return redirect('patients:detail', pk=patient.pk)

    dept, message, reasons = DistributionService.auto_distribute(patient, request.user)

    if dept:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('patients:detail', pk=patient.pk)


@login_required
def auto_distribute_all_view(request):
    if request.method != 'POST':
        return redirect('distribution:queue')

    queue = DistributionService.get_queue()
    success_count = 0
    fail_count = 0

    for patient in queue:
        dept, message, reasons = DistributionService.auto_distribute(patient, request.user)
        if dept:
            success_count += 1
        else:
            fail_count += 1

    messages.info(
        request,
        f'Массовое распределение завершено: распределено {success_count}, '
        f'без распределения {fail_count}.'
    )
    return redirect('distribution:queue')


@login_required
def manual_assign_view(request):
    patient_id = request.GET.get('patient_id')
    if request.method == 'POST':
        form = ManualAssignmentForm(request.POST)
        if form.is_valid():
            patient = form.cleaned_data['patient']
            department = form.cleaned_data['department']
            reason = form.cleaned_data.get('reason', '')

            success, message = DistributionService.assign_patient(
                patient, department, request.user, reason=reason, is_automatic=False
            )
            if success:
                messages.success(request, message)
                return redirect('patients:detail', pk=patient.pk)
            else:
                messages.error(request, message)
    else:
        initial = {}
        if patient_id:
            patient = Patient.objects.filter(pk=patient_id, status='waiting').first()
            if patient:
                initial['patient'] = patient
        form = ManualAssignmentForm(initial=initial)
    return render(request, 'distribution/manual_assign.html', {'form': form})


@login_required
def history_view(request):
    logs = AssignmentLog.objects.select_related(
        'patient', 'from_department', 'to_department', 'assigned_by'
    )
    paginator = Paginator(logs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'distribution/history.html', {'page_obj': page_obj})


@login_required
def department_load_view(request):
    departments = Department.objects.filter(is_active=True).order_by('name')
    return render(request, 'distribution/department_load.html', {'departments': departments})


@login_required
def rules_list_view(request):
    rules = DistributionRule.objects.select_related('department', 'diagnosis').order_by('priority', 'department__name')
    return render(request, 'distribution/rules_list.html', {'rules': rules})


@login_required
def rule_delete_view(request, pk):
    rule = get_object_or_404(DistributionRule, pk=pk)
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Правило распределения удалено.')
        return redirect('distribution:rules_list')
    return render(request, 'distribution/rule_confirm_delete.html', {'rule': rule})
