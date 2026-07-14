import json
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
        self.physical_moderate = PhysicalSeverity.objects.create(name='Средней тяжести', level=2)
        self.physical_heavy = PhysicalSeverity.objects.create(name='Тяжёлое', level=3)
        self.physical_critical = PhysicalSeverity.objects.create(name='Критическое', level=4)
        self.diagnosis_schizo = Diagnosis.objects.create(
            code='F20', name='Шизофрения', block='F20-F29', chapter='Тест'
        )
        self.diagnosis_depression = Diagnosis.objects.create(
            code='F32', name='Депрессия', block='F30-F39', chapter='Тест'
        )
        self.diagnosis_anxiety = Diagnosis.objects.create(
            code='F41', name='Тревожное расстройство', block='F40-F48', chapter='Тест'
        )
        self.dept_schizo = Department.objects.create(
            name='Отделение шизофрении', profile='F20-F29: Шизофрения',
            gender_restriction='ANY', age_category='ADULT',
            total_beds=10, occupied_beds=0
        )
        self.dept_depression = Department.objects.create(
            name='Отделение депрессии', profile='F30-F39: Аффективные',
            gender_restriction='ANY', age_category='ADULT',
            total_beds=10, occupied_beds=0
        )
        self.dept_icu = Department.objects.create(
            name='Отделение интенсивной терапии', profile='Крайне тяжёлые',
            gender_restriction='ANY', age_category='ANY',
            total_beds=5, occupied_beds=0
        )
        self.dept_child = Department.objects.create(
            name='Детское отделение', profile='F80-F98: Дети',
            gender_restriction='ANY', age_category='CHILD',
            total_beds=10, occupied_beds=0
        )
        self.user = User.objects.create_user(
            username='doctor', password='doctor123', role='doctor'
        )

    def test_find_by_diagnosis_block_in_profile(self):
        patient = Patient.objects.create(
            last_name='Тест', first_name='Шизофрения',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_schizo)

    def test_find_by_profile_diagnoses_m2m(self):
        self.dept_schizo.profile_diagnoses.add(self.diagnosis_schizo)
        patient = Patient.objects.create(
            last_name='Тест', first_name='М2М',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_schizo)

    def test_find_depression_goes_to_affective_dept(self):
        patient = Patient.objects.create(
            last_name='Тест', first_name='Депрессия',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_depression,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_depression)

    def test_find_no_suitable_department(self):
        dept_no_beds = Department.objects.create(
            name='Пустое', profile='ZZZ-ZZZ',
            gender_restriction='ANY', age_category='ADULT',
            total_beds=0, occupied_beds=0
        )
        self.dept_schizo.occupied_beds = 10
        self.dept_schizo.save()
        self.dept_depression.occupied_beds = 10
        self.dept_depression.save()
        self.dept_icu.occupied_beds = 5
        self.dept_icu.save()
        self.dept_child.occupied_beds = 10
        self.dept_child.save()
        patient = Patient.objects.create(
            last_name='Нет', first_name='Отделения',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertIsNone(dept)

    def test_extreme_severity_goes_to_icu(self):
        patient = Patient.objects.create(
            last_name='Крайне', first_name='Тяжёлый',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_extreme, physical_severity=self.physical_critical,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_icu)

    def test_high_severity_goes_to_icu(self):
        patient = Patient.objects.create(
            last_name='Тяжёлый', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_heavy, physical_severity=self.physical_heavy,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_icu)

    def test_icu_full_high_severity_falls_to_profile(self):
        self.dept_icu.occupied_beds = 5
        self.dept_icu.save()
        patient = Patient.objects.create(
            last_name='Тяжёлый', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_heavy, physical_severity=self.physical_heavy,
        )
        dept, reasons = DistributionService.find_suitable_department(patient)
        self.assertEqual(dept, self.dept_schizo)

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
        dept, message, reasons = DistributionService.auto_distribute(patient, self.user)
        self.assertEqual(dept, self.dept_schizo)
        patient.refresh_from_db()
        self.assertEqual(patient.status, 'assigned')

    def test_auto_distribute_no_match(self):
        self.dept_schizo.occupied_beds = 10
        self.dept_schizo.save()
        self.dept_depression.occupied_beds = 10
        self.dept_depression.save()
        self.dept_icu.occupied_beds = 5
        self.dept_icu.save()
        self.dept_child.occupied_beds = 10
        self.dept_child.save()
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

    def test_get_queue_sorted_by_severity(self):
        p_light = Patient.objects.create(
            last_name='Лёгкий', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_light, physical_severity=self.physical_good,
            status='waiting'
        )
        p_extreme = Patient.objects.create(
            last_name='Тяжёлый', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_extreme, physical_severity=self.physical_heavy,
            status='waiting'
        )
        p_moderate = Patient.objects.create(
            last_name='Средний', first_name='Тест',
            date_of_birth=date(1988, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_moderate, physical_severity=self.physical_good,
            status='waiting'
        )
        queue = list(DistributionService.get_queue())
        self.assertEqual(queue[0], p_extreme)
        self.assertEqual(queue[1], p_moderate)
        self.assertEqual(queue[2], p_light)

    def test_get_queue_tiebreak_by_date(self):
        from django.utils import timezone
        from datetime import timedelta
        p_earlier = Patient.objects.create(
            last_name='Ранний', first_name='Тест',
            date_of_birth=date(1985, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_heavy, physical_severity=self.physical_heavy,
            status='waiting',
            admission_date=timezone.now() - timedelta(hours=2)
        )
        p_later = Patient.objects.create(
            last_name='Поздний', first_name='Тест',
            date_of_birth=date(1990, 1, 1),
            gender=self.gender_m, diagnosis=self.diagnosis_schizo,
            mental_severity=self.mental_heavy, physical_severity=self.physical_heavy,
            status='waiting',
            admission_date=timezone.now()
        )
        queue = list(DistributionService.get_queue())
        self.assertEqual(queue[0], p_earlier)
        self.assertEqual(queue[1], p_later)

    def test_gender_filtering(self):
        dept_male = Department.objects.create(
            name='Мужское отделение', profile='F20-F29: М',
            gender_restriction='M', age_category='ADULT',
            total_beds=10, occupied_beds=0
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
        response = self.client.get(
            reverse('distribution:auto_distribute', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.status, 'assigned')

    def test_auto_distribute_all_view(self):
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


class AutoDistributeCheckViewTest(TestCase):
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

    def test_check_assigned(self):
        response = self.client.get(
            reverse('distribution:auto_distribute_check', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'assigned')
        self.assertIn('department_name', data)

    def test_check_full_department(self):
        self.dept.occupied_beds = 10
        self.dept.save()
        response = self.client.get(
            reverse('distribution:auto_distribute_check', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'full')
        self.assertIn('department_name', data)
        self.assertIn('patient_id', data)

    def test_check_not_found(self):
        self.dept.occupied_beds = 10
        self.dept.save()
        self.dept.profile = 'ZZZ-ZZZ'
        self.dept.save()
        Department.objects.filter(name='Отделение депрессии').update(occupied_beds=10)
        Department.objects.filter(name='Отделение интенсивной терапии').update(occupied_beds=5)
        Department.objects.filter(name='Детское отделение').update(occupied_beds=10)
        response = self.client.get(
            reverse('distribution:auto_distribute_check', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'not_found')

    def test_check_already_assigned(self):
        self.patient.status = 'assigned'
        self.patient.save()
        response = self.client.get(
            reverse('distribution:auto_distribute_check', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
