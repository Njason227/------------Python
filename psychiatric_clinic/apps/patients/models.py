from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
from apps.references.models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department


class Patient(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Ожидает распределения'),
        ('assigned', 'Распределён'),
        ('hospitalized', 'Госпитализирован'),
        ('rejected', 'Отказ'),
    ]

    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    patronymic = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    date_of_birth = models.DateField(verbose_name='Дата рождения')
    gender = models.ForeignKey(Gender, on_delete=models.PROTECT, verbose_name='Пол')
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.PROTECT, verbose_name='Диагноз (МКБ-11)')
    mental_severity = models.ForeignKey(
        MentalSeverity, on_delete=models.PROTECT, verbose_name='Тяжесть психического состояния'
    )
    physical_severity = models.ForeignKey(
        PhysicalSeverity, on_delete=models.PROTECT, verbose_name='Тяжесть физического состояния'
    )
    admission_date = models.DateTimeField(default=timezone.now, verbose_name='Дата и время поступления')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name='Статус'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Назначенное отделение'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Распределено (врач)'
    )
    assignment_note = models.TextField(blank=True, verbose_name='Примечание к распределению')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'
        ordering = ['-admission_date']

    def __str__(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def age_category(self):
        return 'CHILD' if self.age < 18 else 'ADULT'

    @property
    def age_category_display(self):
        return 'До 18 лет' if self.age < 18 else '18 лет и старше'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'.strip()

    @property
    def severity_priority(self):
        """Числовой приоритет очереди. Чем тяжелее состояние — тем выше приоритет."""
        return self.mental_severity.level + self.physical_severity.level

    @property
    def severity_priority_display(self):
        score = self.severity_priority
        if score >= 7:
            return 'Критический'
        if score >= 5:
            return 'Высокий'
        if score >= 3:
            return 'Средний'
        return 'Низкий'

    @property
    def status_display(self):
        return self.get_status_display()


class AssignmentLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='assignment_logs',
                                verbose_name='Пациент')
    from_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assignments_from', verbose_name='Из отделения'
    )
    to_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assignments_to', verbose_name='В отделение'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Врач'
    )
    reason = models.TextField(blank=True, verbose_name='Причина')
    is_automatic = models.BooleanField(default=False, verbose_name='Автоматическое')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата распределения')

    class Meta:
        verbose_name = 'Лог распределения'
        verbose_name_plural = 'Логи распределений'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.patient} → {self.to_department} ({self.created_at})'
