from apps.references.models import Department, Diagnosis
from apps.patients.models import Patient, AssignmentLog


class DistributionService:
    """Сервис распределения пациентов по отделениям."""

    ICU_KEYWORDS = ['интенсивн', 'реанимац', 'ИТ']

    @staticmethod
    def _diagnosis_matches_department(patient, dept):
        """Проверяет, соответствует ли диагноз пациента профилю отделения."""
        diagnosis = patient.diagnosis
        code = diagnosis.code
        block = diagnosis.block
        prefix3 = code[:3]

        if dept.profile_diagnoses.filter(pk=diagnosis.pk).exists():
            return True

        if dept.profile_diagnoses.filter(code__startswith=prefix3).exists():
            return True

        if block and block in dept.profile:
            return True

        if prefix3 in dept.profile:
            return True

        return False

    @staticmethod
    def _is_icu(dept):
        return any(kw in dept.name.lower() for kw in DistributionService.ICU_KEYWORDS)

    @staticmethod
    def _is_extreme_severity(patient):
        return patient.mental_severity.level == 4 and patient.physical_severity.level == 4

    @staticmethod
    def _is_high_severity(patient):
        return patient.mental_severity.level >= 3 and patient.physical_severity.level >= 3

    @staticmethod
    def _gender_compatible(patient, dept):
        patient_gender = 'M' if patient.gender.name == 'Мужской' else 'F'
        if dept.gender_restriction == 'ANY':
            return True
        return dept.gender_restriction == patient_gender

    @staticmethod
    def _age_compatible(patient, dept):
        if dept.age_category == 'ANY':
            return True
        return dept.age_category == patient.age_category

    @staticmethod
    def find_suitable_department(patient):
        """
        Автоматический поиск подходящего отделения для пациента.
        Логика:
        1. Крайне тяжёлые (4+4) → ИТ, если есть места.
        2. Тяжёлые (3+3 и выше) → ИТ, если есть места.
        3. Диагноз совпадает с профилем отделения → профильное отделение.
        4. Любое отделение с местами и подходящим полом/возрастом.
        Возвращает (отделение, список причин) или (None, список причин отказа).
        """
        patient_gender = 'M' if patient.gender.name == 'Мужской' else 'F'
        patient_age_cat = patient.age_category

        active_depts = Department.objects.filter(is_active=True)

        if DistributionService._is_extreme_severity(patient):
            icu = active_depts.filter(
                gender_restriction__in=['ANY', patient_gender],
            ).filter(
                age_category__in=['ANY', patient_age_cat]
            ).filter(name__icontains='интенсивн').first()

            if not icu:
                icu = active_depts.filter(
                    gender_restriction__in=['ANY', patient_gender],
                    age_category__in=['ANY', patient_age_cat],
                ).filter(name__icontains='реанимац').first()

            if icu and icu.available_beds > 0:
                reasons = [
                    'Крайне тяжёлое состояние (4+4) → отделение интенсивной терапии',
                    f'Пол: {patient.gender.name}',
                    f'Возрастная категория: {patient.age_category_display}',
                    f'Свободных коек: {icu.available_beds}',
                ]
                return icu, reasons

        if DistributionService._is_high_severity(patient):
            icu = active_depts.filter(
                gender_restriction__in=['ANY', patient_gender],
                age_category__in=['ANY', patient_age_cat],
            ).filter(name__icontains='интенсивн').first()

            if not icu:
                icu = active_depts.filter(
                    gender_restriction__in=['ANY', patient_gender],
                    age_category__in=['ANY', patient_age_cat],
                ).filter(name__icontains='реанимац').first()

            if icu and icu.available_beds > 0:
                reasons = [
                    f'Тяжёлое состояние ({patient.mental_severity.level}+{patient.physical_severity.level}) → ИТ',
                    f'Пол: {patient.gender.name}',
                    f'Возрастная категория: {patient.age_category_display}',
                    f'Свободных коек: {icu.available_beds}',
                ]
                return icu, reasons

        profile_depts = []
        for dept in active_depts:
            if not DistributionService._gender_compatible(patient, dept):
                continue
            if not DistributionService._age_compatible(patient, dept):
                continue
            if DistributionService._diagnosis_matches_department(patient, dept):
                profile_depts.append(dept)

        profile_depts.sort(key=lambda d: d.available_beds, reverse=True)
        for dept in profile_depts:
            if dept.available_beds > 0:
                reasons = [
                    f'Диагноз {patient.diagnosis.code} ({patient.diagnosis.block}) совпадает с профилем отделения',
                    f'Пол: {patient.gender.name}',
                    f'Возрастная категория: {patient.age_category_display}',
                    f'Свободных коек: {dept.available_beds}',
                ]
                return dept, reasons

        fallback_depts = []
        for dept in active_depts:
            if not DistributionService._gender_compatible(patient, dept):
                continue
            if not DistributionService._age_compatible(patient, dept):
                continue
            if DistributionService._is_icu(dept):
                continue
            fallback_depts.append(dept)

        fallback_depts.sort(key=lambda d: d.available_beds, reverse=True)
        for dept in fallback_depts:
            if dept.available_beds > 0:
                reasons = [
                    'Нет профильного отделения → отделение общего типа',
                    f'Пол: {patient.gender.name}',
                    f'Возрастная категория: {patient.age_category_display}',
                    f'Свободных коек: {dept.available_beds}',
                ]
                return dept, reasons

        return None, ['Нет подходящих отделений со свободными коек.']

    @staticmethod
    def find_best_department(patient):
        """
        Поиск лучшего подходящего отделения для пациента (включая занятые).
        Возвращает (отделение, список причин) или (None, список причин отказа).
        Используется для проверки возможности распределения (API).
        Не использует общий fallback — только ИТ и профильные отделения.
        """
        patient_gender = 'M' if patient.gender.name == 'Мужской' else 'F'
        patient_age_cat = patient.age_category

        active_depts = Department.objects.filter(is_active=True)

        if DistributionService._is_extreme_severity(patient):
            icu = active_depts.filter(
                gender_restriction__in=['ANY', patient_gender],
            ).filter(
                age_category__in=['ANY', patient_age_cat]
            ).filter(name__icontains='интенсивн').first()

            if not icu:
                icu = active_depts.filter(
                    gender_restriction__in=['ANY', patient_gender],
                    age_category__in=['ANY', patient_age_cat],
                ).filter(name__icontains='реанимац').first()

            if icu:
                reasons = [
                    'Крайне тяжёлое состояние (4+4) → отделение интенсивной терапии',
                    f'Пол: {patient.gender.name}',
                    f'Возрастная категория: {patient.age_category_display}',
                    f'Свободных коек: {icu.available_beds}',
                ]
                return icu, reasons

        if DistributionService._is_high_severity(patient):
            icu = active_depts.filter(
                gender_restriction__in=['ANY', patient_gender],
                age_category__in=['ANY', patient_age_cat],
            ).filter(name__icontains='интенсивн').first()

            if not icu:
                icu = active_depts.filter(
                    gender_restriction__in=['ANY', patient_gender],
                    age_category__in=['ANY', patient_age_cat],
                ).filter(name__icontains='реанимац').first()

            if icu:
                reasons = [
                    f'Тяжёлое состояние ({patient.mental_severity.level}+{patient.physical_severity.level}) → ИТ',
                    f'Пол: {patient.gender.name}',
                    f'Возрастная категория: {patient.age_category_display}',
                    f'Свободных коек: {icu.available_beds}',
                ]
                return icu, reasons

        profile_depts = []
        for dept in active_depts:
            if not DistributionService._gender_compatible(patient, dept):
                continue
            if not DistributionService._age_compatible(patient, dept):
                continue
            if DistributionService._diagnosis_matches_department(patient, dept):
                profile_depts.append(dept)

        profile_depts.sort(key=lambda d: d.available_beds, reverse=True)
        for dept in profile_depts:
            reasons = [
                f'Диагноз {patient.diagnosis.code} ({patient.diagnosis.block}) совпадает с профилем отделения',
                f'Пол: {patient.gender.name}',
                f'Возрастная категория: {patient.age_category_display}',
                f'Свободных коек: {dept.available_beds}',
            ]
            return dept, reasons

        return None, ['Нет подходящих отделений.']

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
        """
        Получение очереди ожидающих распределения.
        Порядок: чем тяжелее состояние пациента (сумма уровней псих. + физ. тяжести),
        тем выше он в очереди. При равной тяжести — ранее поступившие первыми.
        """
        from django.db.models import F, Value, IntegerField
        from django.db.models.functions import Coalesce

        return Patient.objects.filter(
            status='waiting'
        ).select_related(
            'gender', 'diagnosis', 'mental_severity', 'physical_severity'
        ).annotate(
            priority_score=F('mental_severity__level') + F('physical_severity__level')
        ).order_by('-priority_score', 'admission_date')
