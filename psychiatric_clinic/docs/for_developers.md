# Инструкция для разработчиков (агентов)

## Содержание
1. [Обзор архитектуры](#1-обзор-архитектуры)
2. [Структура проекта](#2-структура-проекта)
3. [Конвенции кода](#3-конвенции-кода)
4. [Создание и изменение моделей](#4-создание-и-изменение-моделей)
5. [Добавление новой страницы](#5-добавление-новой-страницы)
6. [Изменение логики распределения](#6-изменение-логики-распределения)
7. [Тестирование](#7-тестирование)
8. [Миграции](#8-миграции)
9. [Частые ошибки](#9-частые-ошибки)

---

## 1. Обзор архитектуры

Приложение построено по паттерну **MVT (Model-View-Template)** на Django 5.x.

### Потоки данных

```
Браузер → URL → View → Service → Model → PostgreSQL
                   ↓
              Template ← Context
```

### Межмодульные связи

```
accounts (User)
    ↓ ForeignKey
references (Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department)
    ↓ ForeignKey
patients (Patient, AssignmentLog)
    ↓ ForeignKey
distribution (DistributionRule, DistributionService)
    ↓
reports (статистика, экспорт)
```

---

## 2. Структура проекта

```
psychiatric_clinic/
├── config/
│   ├── settings.py          # Настройки (БД, Apps, статика)
│   ├── urls.py              # Корневой URL-роутер
│   └── wsgi.py              # WSGI-точка входа
├── apps/
│   ├── accounts/            # Пользователи и роли
│   │   ├── models.py        # User (наследует AbstractUser)
│   │   ├── forms.py         # LoginForm, UserRegistrationForm
│   │   ├── views.py         # login, register, user_list
│   │   ├── urls.py          # accounts:login, accounts:register
│   │   ├── admin.py         # UserAdmin
│   │   └── tests.py
│   ├── references/          # Справочники
│   │   ├── models.py        # Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department
│   │   ├── forms.py         # CRUD-формы для каждого справочника
│   │   ├── views.py         # CRUD-представления
│   │   ├── urls.py          # references:*
│   │   ├── admin.py
│   │   ├── tests.py
│   │   └── management/commands/
│   │       └── load_initial_data.py  # Загрузка начальных данных
│   ├── patients/            # Пациенты
│   │   ├── models.py        # Patient, AssignmentLog
│   │   ├── forms.py         # PatientForm, PatientFilterForm
│   │   ├── views.py         # CRUD + фильтрация
│   │   ├── urls.py          # patients:*
│   │   └── tests.py
│   ├── distribution/        # Распределение
│   │   ├── models.py        # DistributionRule
│   │   ├── services.py      # DistributionService (бизнес-логика)
│   │   ├── forms.py         # ManualAssignmentForm
│   │   ├── views.py         # queue, auto/manual assign, history
│   │   ├── urls.py          # distribution:*
│   │   └── tests.py
│   └── reports/             # Отчётность
│       ├── views.py         # dashboard, export CSV
│       ├── urls.py          # reports:*
│       └── tests.py
├── templates/               # Общие шаблоны (base.html, home.html)
├── static/css/style.css     # Пользовательские стили
├── fixtures/                # Начальные данные (JSON)
├── manage.py
└── requirements.txt
```

### Ключевые файлы для изменений

| Задача | Файлы |
|---|---|
| Новое поле пациента | `patients/models.py`, `patients/forms.py`, шаблоны `patients/`, миграция |
| Новое отделение | `references/models.py`, `load_initial_data.py` или Admin |
| Новое правило распределения | `distribution/models.py`, `distribution/services.py` |
| Новая роль | `accounts/models.py` (ROLE_CHOICES), проверки в `views.py` |
| Новая страница отчёта | `reports/views.py`, `reports/urls.py`, шаблон |

---

## 3. Конвенции кода

### Язык
- Все комментарии, docstring, переменные, названия шаблонов — **на русском языке**
- Python-код — PEP 8

### Django-конвенции

```python
# Модель — всегда __str__, Meta, verbose_name
class MyModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        verbose_name = 'Моя модель'
        verbose_name_plural = 'Мои модели'
        ordering = ['name']

    def __str__(self):
        return self.name

# View — декоратор @login_required, prefix _view
@login_required
def my_view(request):
    ...

# URL — namespace в каждом приложении
app_name = 'my_app'

# Шаблон — наследование от base.html
{% extends "base.html" %}
{% block title %}...{% endblock %}
{% block content %}...{% endblock %}
```

### Формы
- Все виджеты используют CSS-классы Bootstrap 5: `form-control`, `form-select`
- Валидация на стороне клиента и сервера

### Тесты
- Каждый models.py и views.py имеет tests.py
- Тесты покрывают: модели (str, properties), CRUD-операции, авторизацию
- Запуск: `python manage.py test apps.<app_name>.tests`

---

## 4. Создание и изменение моделей

### Пример: добавление нового поля в Patient

**Шаг 1** — `apps/patients/models.py`:

```python
class Patient(models.Model):
    # ... существующие поля ...
    new_field = models.CharField(max_length=100, blank=True, verbose_name='Новое поле')
```

**Шаг 2** — `apps/patients/forms.py`:

```python
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['last_name', 'first_name', ..., 'new_field']
        widgets = {
            # ...
            'new_field': forms.TextInput(attrs={'class': 'form-control'}),
        }
```

**Шаг 3** — Шаблоны `patients/patient_detail.html`, `patient_list.html`, `patient_form.html`:

```html
<tr><td><strong>Новое поле:</strong></td><td>{{ patient.new_field }}</td></tr>
```

**Шаг 4** — Миграция:

```bash
python manage.py makemigrations patients
python manage.py migrate
```

**Шаг 5** — Тесты `apps/patients/tests.py`:

```python
def test_new_field(self):
    patient = Patient.objects.create(..., new_field='значение')
    self.assertEqual(patient.new_field, 'значение')
```

### Связь ForeignKey → новая зависимость

```python
# Всегда используйте PROTECT или SET_NULL, не CASCADE для справочников
new_ref = models.ForeignKey(
    'references.SomeModel',
    on_delete=models.PROTECT,  # запрещает удаление связанного объекта
    verbose_name='Ссылка'
)
```

---

## 5. Добавление новой страницы

### Пошаговый алгоритм

1. **URL** в `apps/<app>/urls.py`:
```python
path('my-page/', views.my_page_view, name='my_page'),
```

2. **View** в `apps/<app>/views.py`:
```python
@login_required
def my_page_view(request):
    context = {'data': MyModel.objects.all()}
    return render(request, 'my_app/my_page.html', context)
```

3. **Шаблон** `apps/<app>/templates/<app>/my_page.html`:
```html
{% extends "base.html" %}
{% block title %}Моя страница{% endblock %}
{% block content %}
<h4 class="mt-3"><i class="bi bi-icon"></i> Моя страница</h4>
<!-- содержимое -->
{% endblock %}
```

4. **Навигация** — добавить ссылку в `templates/base.html` в соответствующее меню.

---

## 6. Изменение логики распределения

Вся бизнес-логика распределения — в файле `apps/distribution/services.py`.

### DistributionService — основной класс

```python
class DistributionService:
    @staticmethod
    def find_suitable_department(patient):
        """Поиск отделения по правилам DistributionRule"""
        ...

    @staticmethod
    def assign_patient(patient, department, user, reason='', is_automatic=False):
        """Назначение в отделение + логирование в AssignmentLog"""
        ...

    @staticmethod
    def auto_distribute(patient, user):
        """Полный цикл: поиск + назначение"""
        ...

    @staticmethod
    def get_queue():
        """Пациенты со статусом 'waiting'"""
        ...
```

### Добавление нового критерия распределения

**Пример**: распределение по наличию сопутствующего заболевания.

1. Добавить поле в модель `Patient`:

```python
has_chronic_disease = models.BooleanField(default=False, verbose_name='Хроническое заболевание')
```

2. Изменить `DistributionService.find_suitable_department`:

```python
for rule in rules:
    # ... существующие проверки ...

    # Новая проверка
    if hasattr(rule, 'requires_chronic_disease'):
        if rule.requires_chronic_disease and not patient.has_chronic_disease:
            continue

    # ... остальной код ...
```

3. Добавить поле в `DistributionRule` (если нужно привязать к правилу):

```python
requires_chronic_disease = models.BooleanField(
    default=False, verbose_name='Требует хроническое заболевание'
)
```

### Порядок проверок в find_suitable_department

```
1. Отделение активно?
2. Есть свободные койки?
3. Соответствие по полу (rule.gender)?
4. Соответствие по возрасту (rule.age_category)?
5. Соответствие по диагнозу (rule.diagnosis)?
6. Соответствие по псих. тяжести?
7. Соответствие по физ. тяжести?
8. Соответствие по полу отделения (dept.gender_restriction)?
9. Соответствие по возрасту отделения (dept.age_category)?
10. → Вернуть отделение
```

---

## 7. Тестирование

### Запуск всех тестов

```bash
python manage.py test apps.accounts.tests apps.references.tests apps.patients.tests apps.distribution.tests apps.reports.tests
```

### Запуск конкретного теста

```bash
python manage.py test apps.distribution.tests.DistributionServiceTest.test_auto_distribute
```

### Структура тестов

```python
class MyAppTest(TestCase):
    def setUp(self):
        # Создание тестовых данных
        self.user = User.objects.create_user(...)
        self.gender = Gender.objects.create(name='Мужской')

    def test_model_str(self):
        self.assertEqual(str(self.obj), '...')

    def test_view_status_code(self):
        self.client.login(username='...', password='...')
        response = self.client.get(reverse('my_app:my_view'))
        self.assertEqual(response.status_code, 200)

    def test_crud_operation(self):
        response = self.client.post(reverse('my_app:create'), {...})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MyModel.objects.count(), 1)
```

### Покрытие тестами

| Приложение | Минимальное покрытие |
|---|---|
| accounts | Все role-свойства, логин/выход, регистрация |
| references | Все CRUD-операции, `__str__`, computed properties |
| patients | CRUD, фильтрация, расчёт возраста, категории |
| distribution | `find_suitable_department`, `assign_patient`, `auto_distribute`, фильтры по полу/возрасту |
| reports | Dashboard, CSV-экспорт, статистика |

---

## 8. Миграции

### Стандартный процесс

```bash
# 1. Изменить модель
# 2. Создать миграцию
python manage.py makemigrations <app_name>

# 3. Проверить (без применения)
python manage.py sqlmigrate <app_name> 0002

# 4. Применить
python manage.py migrate
```

### Откат миграции

```bash
# Откатить последнюю
python manage.py migrate <app_name> 0001
```

### Сброс БД (только для разработки)

```bash
rm db.sqlite3
python manage.py migrate
python manage.py load_initial_data
python manage.py createsuperuser
```

---

## 9. Частые ошибки

### `NoReverseMatch`
Неверный `name` в `{% url %}` или `reverse()`. Проверьте `urls.py` нужного приложения.

### `RelatedObjectDoesNotExist`
Попытка доступа к ForeignKey, который `null=True`, когда объект не задан. Используйте `|default:"..."` в шаблонах.

### `IntegrityError` при удалении
Модель связана через `PROTECT`. Удалите зависимые объекты вручную или смените `on_delete`.

### Миграции не видят модель
Убедитесь, что `__init__.py` существует в каталоге приложения и что приложение добавлено в `INSTALLED_APPS` в формате `apps.<app_name>`.

### Тесты не запускаются
```bash
# Нужно указать полный путь к модулю тестов
python manage.py test apps.<app_name>.tests
```

### Белый экран при отладке
Включите `DEBUG = True` в settings.py для отображения страницы ошибок Django.
