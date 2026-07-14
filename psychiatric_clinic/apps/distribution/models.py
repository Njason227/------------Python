from django.db import models
from django.conf import settings
from apps.references.models import Department, Diagnosis
from apps.patients.models import Patient, AssignmentLog


class DistributionRule(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Первый приоритет'),
        (2, 'Второй приоритет'),
        (3, 'Третий приоритет'),
        (4, 'Четвёртый приоритет'),
        (5, 'Пятый приоритет'),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   related_name='distribution_rules', verbose_name='Отделение')
    diagnosis = models.ForeignKey(
        Diagnosis, on_delete=models.CASCADE, null=True, blank=True,
        related_name='distribution_rules', verbose_name='Диагноз (МКБ-11)'
    )
    gender = models.CharField(
        max_length=1, blank=True, verbose_name='Ограничение по полу (M/F/ANY)'
    )
    age_category = models.CharField(
        max_length=5, blank=True, verbose_name='Возрастная категория (CHILD/ADULT/ANY)'
    )
    min_mental_severity = models.PositiveIntegerField(
        default=1, verbose_name='Мин. тяжесть псих. состояния'
    )
    max_mental_severity = models.PositiveIntegerField(
        default=4, verbose_name='Макс. тяжесть псих. состояния'
    )
    min_physical_severity = models.PositiveIntegerField(
        default=1, verbose_name='Мин. тяжесть физ. состояния'
    )
    max_physical_severity = models.PositiveIntegerField(
        default=4, verbose_name='Макс. тяжесть физ. состояния'
    )
    priority = models.PositiveIntegerField(
        choices=PRIORITY_CHOICES, default=3, verbose_name='Приоритет'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Правило распределения'
        verbose_name_plural = 'Правила распределения'
        ordering = ['priority', 'department__name']

    def __str__(self):
        return f'{self.department.name} (приоритет {self.priority})'
