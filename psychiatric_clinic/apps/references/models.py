from django.db import models


class Gender(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'Пол'
        verbose_name_plural = 'Пол'
        ordering = ['name']

    def __str__(self):
        return self.name


class MentalSeverity(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    level = models.PositiveIntegerField(unique=True, verbose_name='Уровень (1-4)')

    class Meta:
        verbose_name = 'Тяжесть психического состояния'
        verbose_name_plural = 'Тяжести психических состояний'
        ordering = ['level']

    def __str__(self):
        return f'{self.name} (уровень {self.level})'


class PhysicalSeverity(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    level = models.PositiveIntegerField(unique=True, verbose_name='Уровень (1-4)')

    class Meta:
        verbose_name = 'Тяжесть физического состояния'
        verbose_name_plural = 'Тяжести физических состояний'
        ordering = ['level']

    def __str__(self):
        return f'{self.name} (уровень {self.level})'


class Diagnosis(models.Model):
    code = models.CharField(max_length=10, verbose_name='Код МКБ-11')
    name = models.CharField(max_length=500, verbose_name='Название')
    block = models.CharField(max_length=200, blank=True, verbose_name='Блок МКБ')
    chapter = models.CharField(max_length=200, blank=True, verbose_name='Класс МКБ')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', verbose_name='Родительский диагноз'
    )

    class Meta:
        verbose_name = 'Диагноз МКБ-11'
        verbose_name_plural = 'Диагнозы МКБ-11'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def is_block(self):
        return self.children.exists()


class Department(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужское'),
        ('F', 'Женское'),
        ('ANY', 'Смешанное'),
    ]
    AGE_CHOICES = [
        ('CHILD', 'Детское/Подростковое'),
        ('ADULT', 'Взрослое'),
        ('ANY', 'Любой возраст'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название отделения')
    profile = models.CharField(max_length=500, blank=True, verbose_name='Профиль (диагнозы)')
    profile_diagnoses = models.ManyToManyField(
        Diagnosis, blank=True, related_name='departments', verbose_name='Профильные диагнозы'
    )
    gender_restriction = models.CharField(
        max_length=3, choices=GENDER_CHOICES, default='ANY', verbose_name='Ограничение по полу'
    )
    age_category = models.CharField(
        max_length=5, choices=AGE_CHOICES, default='ANY', verbose_name='Возрастная категория'
    )
    total_beds = models.PositiveIntegerField(default=0, verbose_name='Общее кол-во коек')
    occupied_beds = models.PositiveIntegerField(default=0, verbose_name='Занято коек')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Отделение'
        verbose_name_plural = 'Отделения'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def available_beds(self):
        return max(0, self.total_beds - self.occupied_beds)

    @property
    def occupancy_percent(self):
        if self.total_beds == 0:
            return 0
        return round(self.occupied_beds / self.total_beds * 100, 1)
