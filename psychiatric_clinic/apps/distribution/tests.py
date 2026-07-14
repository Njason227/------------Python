from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from .models import DistributionRule
from .services import DistributionService
from apps.references.models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department
from apps.patients.models import Patient, AssignmentLog
from apps.accounts.models import User


class DistributionServiceTest(TestCase):
    def setUp(self):
        self.gender_m = Gender.objects.create(name='Мужской')
        self.gender_f = Gender.objects.create(name='Женский')
        self.mental_light = MentalSeverity.objects.create(name='Лёгкая', level=1)
        self.mental_moderate = MentalSeverity.objects.create(name='Умеренная', level=2)
        self.mental_heavy = MentalSeverity.objects.create(name='Тяжёлая', level=3)
        self.mental_extreme = MentalSeverity.objects.create(name='Крайне тяжёлая', level=4)
        self.physical_good = PhysicalSeverity.objects.create(name='Удовлетворительное', level=1)
        self.physical_heavy = PhysicalSeverity.objects.create(name='Тяжёлое', level=3)
        self.diagnosis_schizo = Diagnosis.objects.create(
            code='F20', name='Шизофрения', block='F20-F29', chapter='Тест'
        )
        self.diagnosis_depression = Diagnosis.objects.create(
            code='F32', name='Депрессия', block='F30-F39', chapter='Тест'
        )
        self.dept_schizo = Department.objects.create(
            name='Отделение шизофрении', profile='F20-F29',
            gender_restriction='ANY', age_category='ADULT',
            total_beds=10, occupied_beds=0
        )
        self.dept_depression = Department.objects.create(
            name='Отделение депрессии', profile='F30-F39',
            gender_restriction='ANY', age_category='ADULT',
            total_beds=10, occupied_beds=0
        )
        self.dept_child = Department.objects.create(
            name='Детское отделение', profile='Дети',
            gender_restriction='ANY', age_category='CHILD',
            total_beds=10, occupied_beds=0
        )
        self.user = User.objects.create_user(
            username='doctor', password='doctor123', role='doctor'
        )

    def test_find_suitable_department_by_diagnosis(self):
        patient = Patient.objects.create(
            last_name='Тест', first_name='Шизофрения',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        rule = DistributionRule.objects.create(
            department=self.dept_schizo, diagnosis=self.diagnosis_schizo,
            priority=1
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_schizo)

    def test_find_no_suitable_department(self):
        patient = Patient.objects.create(
            last_name='Нет', first_name='Отделения',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertIsNone(dept)

    def test_assign_patient(self):
        patient = Patient.objects.create(
            last_name='Назначение', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        success, message = DistributionService.assign_patient(
            patient, self.dept_schizo, self.user, reason='Тестовое назначение'
        )
        self.assertTrue(success)
        patient.refresh_from_db()
        self.assertEqual(patient.department, self.dept_schizo)
        self.assertEqual(patient.status, 'assigned')
        self.dept_schizo.refresh_from_db()
        self.assertEqual(self.dept_schizo.occupied_beds, 1)

    def test_assign_to_full_department(self):
        self.dept_schizo.occupied_beds = 10
        self.dept_schizo.save()
        patient = Patient.objects.create(
            last_name='Полный', first_name='Отделение',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        success, message = DistributionService.assign_patient(
            patient, self.dept_schizo, self.user
        )
        self.assertFalse(success)

    def test_auto_distribute(self):
        patient = Patient.objects.create(
            last_name='Авто', first_name='Распределение',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        rule = DistributionRule.objects.create(
            department=self.dept_schizo, diagnosis=self.diagnosis_schizo,
            priority=1
        )
        dept, message, reasons = DistributionService.auto_distribute(patient, self.user)
        self.assertEqual(dept, self.dept_schizo)
        patient.refresh_from_db()
        self.assertEqual(patient.status, 'assigned')

    def test_auto_distribute_no_match(self):
        patient = Patient.objects.create(
            last_name='Нет', first_name='Совпадения',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, message, reasons = DistributionService.auto_distribute(patient, self.user)
        self.assertIsNone(dept)

    def test_get_queue(self):
        p1 = Patient.objects.create(
            last_name='Один', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
            status='waiting'
        )
        p2 = Patient.objects.create(
            last_name='Два', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender_f, diagnosis=self.diagnosis_depression,
            mental_severity=self.mental_moderate, physical_severity=self.physical_good,
            status='assigned'
        )
        queue = DistributionService.get_queue()
        self.assertEqual(queue.count(), 1)
        self.assertEqual(queue.first(), p1)

    def test_gender_filtering(self):
        dept_male = Department.objects.create(
            name='Мужское отделение', profile='М',
            gender_restriction='M', age_category='ADULT',
            total_beds=10, occupied_beds=0
        )
        rule = DistributionRule.objects.create(
            department=dept_male, priority=1, gender='M'
        )
        female_patient = Patient.objects.create(
            last_name='Женщина', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_f, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(female_patient)
        self.assertNotEqual(dept, dept_male)

    def test_age_category_filtering(self):
        rule = DistributionRule.objects.create(
            department=self.dept_child, priority=1, age_category='CHILD'
        )
        adult_patient = Patient.objects.create(
            last_name='Взрослый', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(adult_patient)
        self.assertNotEqual(dept, self.dept_child)


class DistributionViewsTest(TestCase):
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
            name='Отделение', profile='F20-F29',
            total_beds=10, occupied_beds=0
        )
        self.patient = Patient.objects.create(
            last_name='Пациент', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender, diagnosis=self.diagnosis,
            mental_severity=self.mental, physical_severity=self.physical,
            status='waiting'
        )

    def test_queue_view(self):
        response = self.client.get(reverse('distribution:queue'))
        self.assertEqual(response.status_code, 200)

    def test_auto_distribute_view(self):
        rule = DistributionRule.objects.create(
            department=self.dept, diagnosis=self.diagnosis, priority=1
        )
        response = self.client.get(
            reverse('distribution:auto_distribute', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.status, 'assigned')

    def test_auto_distribute_all_view(self):
        rule = DistributionRule.objects.create(
            department=self.dept, diagnosis=self.diagnosis, priority=1
        )
        response = self.client.post(reverse('distribution:auto_distribute_all'))
        self.assertEqual(response.status_code, 302)

    def test_manual_assign_view(self):
        response = self.client.get(reverse('distribution:manual_assign'))
        self.assertEqual(response.status_code, 200)

    def test_manual_assign_post(self):
        response = self.client.post(reverse('distribution:manual_assign'), {
            'patient': self.patient.pk,
            'department': self.dept.pk,
            'reason': 'Ручное назначение',
        })
        self.assertEqual(response.status_code, 302)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.status, 'assigned')

    def test_history_view(self):
        response = self.client.get(reverse('distribution:history'))
        self.assertEqual(response.status_code, 200)

    def test_department_load_view(self):
        response = self.client.get(reverse('distribution:department_load'))
        self.assertEqual(response.status_code, 200)

    def test_rules_list_view(self):
        response = self.client.get(reverse('distribution:rules_list'))
        self.assertEqual(response.status_code, 200)

    def test_rule_delete_view(self):
        rule = DistributionRule.objects.create(
            department=self.dept, priority=1
        )
        response = self.client.post(reverse('distribution:rule_delete', args=[rule.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DistributionRule.objects.count(), 0)

    def test_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('distribution:queue'))
        self.assertEqual(response.status_code, 302)
