from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from .views import home_redirect
from apps.references.models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department
from apps.patients.models import Patient
from apps.accounts.models import User


class ReportsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='doctor', password='doctor123', role='doctor'
        )
        self.client.login(username='doctor', password='doctor123')
        self.gender = Gender.objects.create(name='Мужской')
        self.mental = MentalSeverity.objects.create(name='Лёгкая', level=1)
        self.physical = PhysicalSeverity.objects.create(name='Удовлетворительное', level=1)
        self.diagnosis = Diagnosis.objects.create(
            code='F20', name='Шизофрения', block='F20-F29', chapter='Тест'
        )
        self.dept = Department.objects.create(
            name='Отделение', total_beds=10, occupied_beds=0
        )

    def test_home_authenticated(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view(self):
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_with_patients(self):
        Patient.objects.create(
            last_name='Тест', first_name='Пациент',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
            status='waiting'
        )
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_export_csv(self):
        Patient.objects.create(
            last_name='Экспорт', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
        )
        response = self.client.get(reverse('reports:export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')

    def test_export_csv_empty(self):
        response = self.client.get(reverse('reports:export_csv'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('reports:dashboard'))
        self.assertEqual(response.status_code, 302)
