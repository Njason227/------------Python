from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, UserRegistrationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('patients:list')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('patients:list')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def register_view(request):
    if not request.user.is_admin_role and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для создания пользователей.')
        return redirect('patients:list')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пользователь успешно создан.')
            return redirect('accounts:user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def user_list_view(request):
    if not request.user.is_admin_role and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для просмотра пользователей.')
        return redirect('patients:list')
    users = User.objects.all().order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})
