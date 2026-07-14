from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('doctor', 'Врач приёмного отделения'),
        ('senior_nurse', 'Старшая медсестра'),
        ('admin', 'Администратор'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='doctor', verbose_name='Роль')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_role_display()})'

    @property
    def is_doctor(self):
        return self.role == 'doctor'

    @property
    def is_senior_nurse(self):
        return self.role == 'senior_nurse'

    @property
    def is_admin_role(self):
        return self.role == 'admin'
