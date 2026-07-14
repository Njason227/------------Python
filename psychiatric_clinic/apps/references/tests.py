from django.test import TestCase, Client
from django.urls import reverse
from .models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department
from apps.accounts.models import User


class ReferenceModelsTest(TestCase):
    def setUp(self):
        self.gender = Gender.objects.create(name='Мужской')
        self.mental = MentalSeverity.objects.create(name='Лёгкая', level=1)
        self.physical = PhysicalSeverity.objects.create(name='Удовлетворительное', level=1)
        self.diagnosis = Diagnosis.objects.create(
            code='F20', name='Шизофрения', block='F20-F29',
            chapter='Шизофрения и другие психотические расстройства'
        )
        self.department = Department.objects.create(
            name='Тестовое отделение', profile='Тест',
            gender_restriction='ANY', age_category='ADULT',
            total_beds=10, occupied_beds=3
        )

    def test_gender_str(self):
        self.assertEqual(str(self.gender), 'Мужской')

    def test_mental_severity_str(self):
        self.assertEqual(str(self.mental), 'Лёгкая (уровень 1)')

    def test_physical_severity_str(self):
        self.assertEqual(str(self.physical), 'Удовлетворительное (уровень 1)')

    def test_diagnosis_str(self):
        self.assertEqual(str(self.diagnosis), 'F20 - Шизофрения')

    def test_department_str(self):
        self.assertEqual(str(self.department), 'Тестовое отделение')

    def test_department_available_beds(self):
        self.assertEqual(self.department.available_beds, 7)

    def test_department_occupancy_percent(self):
        self.assertEqual(self.department.occupancy_percent, 30.0)

    def test_department_no_beds(self):
        dept = Department.objects.create(name='Empty', total_beds=0, occupied_beds=0)
        self.assertEqual(dept.occupancy_percent, 0)


class ReferenceViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123', role='admin'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_index_view(self):
        response = self.client.get(reverse('references:index'))
        self.assertEqual(response.status_code, 200)

    def test_gender_list(self):
        response = self.client.get(reverse('references:gender_list'))
        self.assertEqual(response.status_code, 200)

    def test_gender_create(self):
        response = self.client.post(reverse('references:gender_create'), {'name': 'Женский'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Gender.objects.count(), 1)

    def test_gender_edit(self):
        gender = Gender.objects.create(name='Тест')
        response = self.client.post(reverse('references:gender_edit', args=[gender.pk]), {'name': 'Обновлённый'})
        self.assertEqual(response.status_code, 302)
        gender.refresh_from_db()
        self.assertEqual(gender.name, 'Обновлённый')

    def test_gender_delete(self):
        gender = Gender.objects.create(name='Удалить')
        response = self.client.post(reverse('references:gender_delete', args=[gender.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Gender.objects.count(), 0)

    def test_diagnosis_list(self):
        response = self.client.get(reverse('references:diagnosis_list'))
        self.assertEqual(response.status_code, 200)

    def test_diagnosis_search(self):
        Diagnosis.objects.create(code='F20', name='Шизофрения', block='F20-F29', chapter='Тест')
        response = self.client.get(reverse('references:diagnosis_list') + '?q=F20')
        self.assertEqual(response.status_code, 200)

    def test_department_list(self):
        response = self.client.get(reverse('references:department_list'))
        self.assertEqual(response.status_code, 200)

    def test_department_create(self):
        response = self.client.post(reverse('references:department_create'), {
            'name': 'Новое отделение',
            'profile': 'Тестовый профиль',
            'gender_restriction': 'ANY',
            'age_category': 'ADULT',
            'total_beds': 20,
            'occupied_beds': 0,
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Department.objects.count(), 1)

    def test_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('references:gender_list'))
        self.assertEqual(response.status_code, 302)
