from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from .models import Patient, AssignmentLog
from apps.references.models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department
from apps.accounts.models import User


class PatientModelTest(TestCase):
    def setUp(self):
        self.gender = Gender.objects.create(name='Мужской')
        self.mental = MentalSeverity.objects.create(name='Лёгкая', level=1)
        self.physical = PhysicalSeverity.objects.create(name='Удовлетворительное', level=1)
        self.diagnosis = Diagnosis.objects.create(
            code='F20', name='Шизофрения', block='F20-F29', chapter='Тест'
        )
        self.patient = Patient.objects.create(
            last_name='Иванов', first_name='Иван', patronymic='Иванович',
            date_of_birth=date(1990, 5, 15),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )

    def test_patient_str(self):
        self.assertEqual(str(self.patient), 'Иванов Иван Иванович')

    def test_patient_full_name(self):
        self.assertEqual(self.patient.full_name, 'Иванов Иван Иванович')

    def test_patient_age(self):
        today = date.today()
        expected_age = today.year - 1990 - ((today.month, today.day) < (5, 15))
        self.assertEqual(self.patient.age, expected_age)

    def test_patient_age_category_adult(self):
        self.assertEqual(self.patient.age_category, 'ADULT')
        self.assertEqual(self.patient.age_category_display, '18 лет и старше')

    def test_patient_age_category_child(self):
        child_patient = Patient.objects.create(
            last_name='Ребёнок', first_name='Тест',
            date_of_birth=date.today() - timedelta(days=365*10),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )
        self.assertEqual(child_patient.age_category, 'CHILD')
        self.assertEqual(child_patient.age_category_display, 'До 18 лет')

    def test_patient_status_display(self):
        self.assertEqual(self.patient.status_display, 'Ожидает распределения')

    def test_severity_priority_light(self):
        self.assertEqual(self.patient.severity_priority, 2)
        self.assertEqual(self.patient.severity_priority_display, 'Низкий')

    def test_severity_priority_extreme(self):
        mental = MentalSeverity.objects.create(name='Крайне тяжёлая', level=4)
        physical = PhysicalSeverity.objects.create(name='Критическое', level=4)
        patient = Patient.objects.create(
            last_name='Тяжёлый', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=mental, physical_severity=physical,
        )
        self.assertEqual(patient.severity_priority, 8)
        self.assertEqual(patient.severity_priority_display, 'Критический')

    def test_severity_priority_moderate(self):
        mental = MentalSeverity.objects.create(name='Умеренная', level=2)
        physical = PhysicalSeverity.objects.create(name='Средней тяжести', level=2)
        patient = Patient.objects.create(
            last_name='Средний', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=mental, physical_severity=physical,
        )
        self.assertEqual(patient.severity_priority, 4)
        self.assertEqual(patient.severity_priority_display, 'Средний')

    def test_assignment_log_str(self):
        dept = Department.objects.create(name='Отделение', total_beds=10)
        log = AssignmentLog.objects.create(
            patient=self.patient, to_department=dept, is_automatic=False
        )
        self.assertIn(self.patient.full_name, str(log))


class PatientViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', role='doctor'
        )
        self.client.login(username='testuser', password='testpass123')
        self.gender = Gender.objects.create(name='Мужской')
        self.mental = MentalSeverity.objects.create(name='Лёгкая', level=1)
        self.physical = PhysicalSeverity.objects.create(name='Удовлетворительное', level=1)
        self.diagnosis = Diagnosis.objects.create(
            code='F20', name='Шизофрения', block='F20-F29', chapter='Тест'
        )

    def test_patient_list(self):
        response = self.client.get(reverse('patients:list'))
        self.assertEqual(response.status_code, 200)

    def test_patient_create(self):
        response = self.client.post(reverse('patients:create'), {
            'last_name': 'Петров',
            'first_name': 'Пётр',
            'patronymic': 'Петрович',
            'date_of_birth': '1985-03-20',
            'gender': self.gender.pk,
            'diagnosis': self.diagnosis.pk,
            'mental_severity': self.mental.pk,
            'physical_severity': self.physical.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Patient.objects.count(), 1)

    def test_patient_detail(self):
        patient = Patient.objects.create(
            last_name='Тест', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )
        response = self.client.get(reverse('patients:detail', args=[patient.pk]))
        self.assertEqual(response.status_code, 200)

    def test_patient_edit(self):
        patient = Patient.objects.create(
            last_name='До', first_name='Редакции',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )
        response = self.client.post(reverse('patients:edit', args=[patient.pk]), {
            'last_name': 'После',
            'first_name': 'Редакции',
            'patronymic': '',
            'date_of_birth': '1990-01-01',
            'gender': self.gender.pk,
            'diagnosis': self.diagnosis.pk,
            'mental_severity': self.mental.pk,
            'physical_severity': self.physical.pk,
        })
        self.assertEqual(response.status_code, 302)
        patient.refresh_from_db()
        self.assertEqual(patient.last_name, 'После')

    def test_patient_delete(self):
        patient = Patient.objects.create(
            last_name='Удалить', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )
        response = self.client.post(reverse('patients:delete', args=[patient.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Patient.objects.count(), 0)

    def test_patient_list_filter(self):
        Patient.objects.create(
            last_name='Фильтр', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )
        response = self.client.get(reverse('patients:list') + '?q=Фильтр')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('patients:list'))
        self.assertEqual(response.status_code, 302)
