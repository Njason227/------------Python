from apps.references.models import Department
from apps.patients.models import Patient, AssignmentLog
from .models import DistributionRule


class DistributionService:
    """Сервис распределения пациентов по отделениям."""

    @staticmethod
    def find_suitable_department(patient):
        """
        Поиск подходящего отделения для пациента на основании правил распределения.
        Возвращает (отделение, список причин) или (None, список причин отказа).
        """
        rules = DistributionRule.objects.filter(
            is_active=True
        ).select_related('department', 'diagnosis').order_by('priority', '-department__occupied_beds')

        patient_gender = 'M' if patient.gender.name == 'Мужской' else 'F'
        patient_age_cat = patient.age_category

        for rule in rules:
            dept = rule.department

            if not dept.is_active:
                continue

            if dept.available_beds <= 0:
                continue

            reasons = []

            if rule.gender and rule.gender != 'ANY':
                if rule.gender != patient_gender:
                    continue

            if rule.age_category and rule.age_category != 'ANY':
                if rule.age_category != patient_age_cat:
                    continue

            if rule.diagnosis:
                diagnosis_code = patient.diagnosis.code
                rule_code = rule.diagnosis.code
                if not (diagnosis_code.startswith(rule_code[:3]) or diagnosis_code == rule_code):
                    continue

            if not (rule.min_mental_severity <= patient.mental_severity.level <= rule.max_mental_severity):
                continue

            if not (rule.min_physical_severity <= patient.physical_severity.level <= rule.max_physical_severity):
                continue

            if dept.gender_restriction != 'ANY' and dept.gender_restriction != patient_gender:
                continue

            if dept.age_category != 'ANY' and dept.age_category != patient_age_cat:
                continue

            reasons.append(f'Правило: приоритет {rule.priority}')
            if rule.diagnosis:
                reasons.append(f'Диагноз совпадает с профилем отделения ({rule.diagnosis.code})')
            reasons.append(f'Пол: соответствует ({patient.gender.name})')
            reasons.append(f'Возрастная категория: {patient.age_category_display}')
            reasons.append(f'Тяжесть псих. состояния: уровень {patient.mental_severity.level}')
            reasons.append(f'Тяжесть физ. состояния: уровень {patient.physical_severity.level}')
            reasons.append(f'Свободных коек: {dept.available_beds}')

            return dept, reasons

        fallback_rules = DistributionRule.objects.filter(
            is_active=True,
            department__is_active=True,
        ).select_related('department').order_by('priority')

        for rule in fallback_rules:
            dept = rule.department
            if dept.available_beds <= 0:
                continue
            if dept.gender_restriction != 'ANY' and dept.gender_restriction != patient_gender:
                continue
            if dept.age_category != 'ANY' and dept.age_category != patient_age_cat:
                continue
            reasons = [
                'Отделение выбрано по общему правилу (нет точного совпадения)',
                f'Свободных коек: {dept.available_beds}',
            ]
            return dept, reasons

        return None, ['Нет подходящих отделений со свободными коек.']

    @staticmethod
    def assign_patient(patient, department, user, reason='', is_automatic=False):
        """
        Назначение пациента в отделение.
        Возвращает (success: bool, message: str).
        """
        if department.available_beds <= 0:
            return False, 'В отделении нет свободных коек.'

        from_department = patient.department

        if from_department:
            from_department.occupied_beds = max(0, from_department.occupied_beds - 1)
            from_department.save()

        patient.department = department
        patient.assigned_by = user
        patient.status = 'assigned'
        if reason:
            patient.assignment_note = reason
        patient.save()

        department.occupied_beds += 1
        department.save()

        AssignmentLog.objects.create(
            patient=patient,
            from_department=from_department,
            to_department=department,
            assigned_by=user,
            reason=reason,
            is_automatic=is_automatic,
        )

        return True, f'Пациент распределён в отделение «{department.name}».'

    @staticmethod
    def auto_distribute(patient, user):
        """
        Автоматическое распределение пациента.
        Возвращает (отделение, сообщение, список причин).
        """
        dept, reasons = DistributionService.find_suitable_department(patient)
        if dept is None:
            return None, 'Не удалось найти подходящее отделение.', reasons

        reason_text = '\n'.join(reasons)
        success, message = DistributionService.assign_patient(
            patient, dept, user, reason=reason_text, is_automatic=True
        )

        return dept, message, reasons

    @staticmethod
    def get_queue():
        """Получение очереди ожидающих распределения."""
        return Patient.objects.filter(
            status='waiting'
        ).select_related(
            'gender', 'diagnosis', 'mental_severity', 'physical_severity'
        ).order_by('-admission_date')
