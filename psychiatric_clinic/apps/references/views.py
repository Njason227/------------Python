from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department
from .forms import (
    GenderForm, MentalSeverityForm, PhysicalSeverityForm,
    DiagnosisForm, DepartmentForm
)


@login_required
def index_view(request):
    return render(request, 'references/index.html')


@login_required
def gender_list_view(request):
    items = Gender.objects.all()
    return render(request, 'references/gender_list.html', {'items': items})


@login_required
def gender_create_view(request):
    if request.method == 'POST':
        form = GenderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пол добавлен.')
            return redirect('references:gender_list')
    else:
        form = GenderForm()
    return render(request, 'references/form.html', {'form': form, 'title': 'Добавить пол'})


@login_required
def gender_edit_view(request, pk):
    item = get_object_or_404(Gender, pk=pk)
    if request.method == 'POST':
        form = GenderForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пол обновлён.')
            return redirect('references:gender_list')
    else:
        form = GenderForm(instance=item)
    return render(request, 'references/form.html', {'form': form, 'title': 'Редактировать пол'})


@login_required
def gender_delete_view(request, pk):
    item = get_object_or_404(Gender, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Пол удалён.')
        return redirect('references:gender_list')
    return render(request, 'references/confirm_delete.html', {'object': item, 'title': 'Удалить пол'})


@login_required
def mental_severity_list_view(request):
    items = MentalSeverity.objects.all()
    return render(request, 'references/mental_severity_list.html', {'items': items})


@login_required
def mental_severity_create_view(request):
    if request.method == 'POST':
        form = MentalSeverityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тяжесть психического состояния добавлена.')
            return redirect('references:mental_severity_list')
    else:
        form = MentalSeverityForm()
    return render(request, 'references/form.html', {'form': form, 'title': 'Добавить тяжесть псих. состояния'})


@login_required
def mental_severity_edit_view(request, pk):
    item = get_object_or_404(MentalSeverity, pk=pk)
    if request.method == 'POST':
        form = MentalSeverityForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тяжесть психического состояния обновлена.')
            return redirect('references:mental_severity_list')
    else:
        form = MentalSeverityForm(instance=item)
    return render(request, 'references/form.html', {'form': form, 'title': 'Редактировать тяжесть псих. состояния'})


@login_required
def mental_severity_delete_view(request, pk):
    item = get_object_or_404(MentalSeverity, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Тяжесть психического состояния удалена.')
        return redirect('references:mental_severity_list')
    return render(request, 'references/confirm_delete.html', {'object': item, 'title': 'Удалить тяжесть псих. состояния'})


@login_required
def physical_severity_list_view(request):
    items = PhysicalSeverity.objects.all()
    return render(request, 'references/physical_severity_list.html', {'items': items})


@login_required
def physical_severity_create_view(request):
    if request.method == 'POST':
        form = PhysicalSeverityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тяжесть физического состояния добавлена.')
            return redirect('references:physical_severity_list')
    else:
        form = PhysicalSeverityForm()
    return render(request, 'references/form.html', {'form': form, 'title': 'Добавить тяжесть физ. состояния'})


@login_required
def physical_severity_edit_view(request, pk):
    item = get_object_or_404(PhysicalSeverity, pk=pk)
    if request.method == 'POST':
        form = PhysicalSeverityForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тяжесть физического состояния обновлена.')
            return redirect('references:physical_severity_list')
    else:
        form = PhysicalSeverityForm(instance=item)
    return render(request, 'references/form.html', {'form': form, 'title': 'Редактировать тяжесть физ. состояния'})


@login_required
def physical_severity_delete_view(request, pk):
    item = get_object_or_404(PhysicalSeverity, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Тяжесть физического состояния удалена.')
        return redirect('references:physical_severity_list')
    return render(request, 'references/confirm_delete.html', {'object': item, 'title': 'Удалить тяжесть физ. состояния'})


@login_required
def diagnosis_list_view(request):
    query = request.GET.get('q', '')
    items = Diagnosis.objects.all()
    if query:
        items = items.filter(name__icontains=query) | items.filter(code__icontains=query)
    items = items.order_by('code')
    return render(request, 'references/diagnosis_list.html', {'items': items, 'query': query})


@login_required
def diagnosis_create_view(request):
    if request.method == 'POST':
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Диагноз добавлен.')
            return redirect('references:diagnosis_list')
    else:
        form = DiagnosisForm()
    return render(request, 'references/form.html', {'form': form, 'title': 'Добавить диагноз МКБ-11'})


@login_required
def diagnosis_edit_view(request, pk):
    item = get_object_or_404(Diagnosis, pk=pk)
    if request.method == 'POST':
        form = DiagnosisForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Диагноз обновлён.')
            return redirect('references:diagnosis_list')
    else:
        form = DiagnosisForm(instance=item)
    return render(request, 'references/form.html', {'form': form, 'title': 'Редактировать диагноз МКБ-11'})


@login_required
def diagnosis_delete_view(request, pk):
    item = get_object_or_404(Diagnosis, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Диагноз удалён.')
        return redirect('references:diagnosis_list')
    return render(request, 'references/confirm_delete.html', {'object': item, 'title': 'Удалить диагноз'})


@login_required
def department_list_view(request):
    items = Department.objects.all()
    return render(request, 'references/department_list.html', {'items': items})


@login_required
def department_create_view(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отделение добавлено.')
            return redirect('references:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'references/form.html', {'form': form, 'title': 'Добавить отделение'})


@login_required
def department_edit_view(request, pk):
    item = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отделение обновлено.')
            return redirect('references:department_list')
    else:
        form = DepartmentForm(instance=item)
    return render(request, 'references/form.html', {'form': form, 'title': 'Редактировать отделение'})


@login_required
def department_delete_view(request, pk):
    item = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Отделение удалено.')
        return redirect('references:department_list')
    return render(request, 'references/confirm_delete.html', {'object': item, 'title': 'Удалить отделение'})
