import json
from django.core.management.base import BaseCommand
from apps.references.models import Gender, MentalSeverity, PhysicalSeverity, Diagnosis, Department


class Command(BaseCommand):
    help = 'Загрузка начальных данных для справочников'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка начальных данных...')

        genders = [('Мужской',), ('Женский',)]
        for (name,) in genders:
            Gender.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f'Загружено {len(genders)} полов'))

        mental_severities = [
            ('Лёгкая', 1), ('Умеренная', 2), ('Тяжёлая', 3), ('Крайне тяжёлая', 4),
        ]
        for name, level in mental_severities:
            MentalSeverity.objects.get_or_create(name=name, defaults={'level': level})
        self.stdout.write(self.style.SUCCESS(f'Загружено {len(mental_severities)} тяжестей псих. состояний'))

        physical_severities = [
            ('Удовлетворительное', 1), ('Средней тяжести', 2),
            ('Тяжёлое', 3), ('Критическое', 4),
        ]
        for name, level in physical_severities:
            PhysicalSeverity.objects.get_or_create(name=name, defaults={'level': level})
        self.stdout.write(self.style.SUCCESS(f'Загружено {len(physical_severities)} тяжестей физ. состояний'))

        diagnoses_data = [
            {'code': 'F00', 'name': 'Деменция при болезни Альцгеймера', 'block': 'F00-F09', 'chapter': 'Нейрокогнитивные расстройства'},
            {'code': 'F01', 'name': 'Деменция при сосудистых заболеваниях головного мозга', 'block': 'F00-F09', 'chapter': 'Нейрокогнитивные расстройства'},
            {'code': 'F06', 'name': 'Психические расстройства при других заболеваниях головного мозга', 'block': 'F00-F09', 'chapter': 'Нейрокогнитивные расстройства'},
            {'code': 'F10', 'name': 'Психические и поведенческие расстройства, вызванные употреблением алкоголя', 'block': 'F10-F19', 'chapter': 'Психические расстройства, связанные с употреблением ПАВ'},
            {'code': 'F20', 'name': 'Шизофрения', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F20.0', 'name': 'Параноидная шизофрения', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F20.1', 'name': 'Гебефреническая шизофрения', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F20.2', 'name': 'Кататоническая шизофрения', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F20.3', 'name': 'Недифференцированная шизофрения', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F21', 'name': 'Шизотипическое расстройство', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F22', 'name': 'Бредовые расстройства', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F23', 'name': 'Острые и переходные психотические расстройства', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F24', 'name': 'Индуцированное бредовое расстройство', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F25', 'name': 'Шизоаффективные расстройства', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F28', 'name': 'Другие психотические расстройства', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F29', 'name': 'Неуточнённое психотическое расстройство', 'block': 'F20-F29', 'chapter': 'Шизофрения и другие психотические расстройства'},
            {'code': 'F30', 'name': 'Маниакальный эпизод', 'block': 'F30-F39', 'chapter': 'Расстройства настроения (аффективные расстройства)'},
            {'code': 'F31', 'name': 'Биполярное аффективное расстройство', 'block': 'F30-F39', 'chapter': 'Расстройства настроения (аффективные расстройства)'},
            {'code': 'F32', 'name': 'Депрессивный эпизод', 'block': 'F30-F39', 'chapter': 'Расстройства настроения (аффективные расстройства)'},
            {'code': 'F33', 'name': 'Рекуррентное депрессивное расстройство', 'block': 'F30-F39', 'chapter': 'Расстройства настроения (аффективные расстройства)'},
            {'code': 'F34', 'name': 'Циклотимия', 'block': 'F30-F39', 'chapter': 'Расстройства настроения (аффективные расстройства)'},
            {'code': 'F40', 'name': 'Фобические тревожные расстройства', 'block': 'F40-F48', 'chapter': 'Тревожные расстройства'},
            {'code': 'F41', 'name': 'Другие тревожные расстройства', 'block': 'F40-F48', 'chapter': 'Тревожные расстройства'},
            {'code': 'F42', 'name': 'Обсессивно-компульсивное расстройство', 'block': 'F40-F48', 'chapter': 'Тревожные расстройства'},
            {'code': 'F43', 'name': 'Реакция на тяжёлый стресс и нарушения адаптации', 'block': 'F40-F48', 'chapter': 'Тревожные расстройства'},
            {'code': 'F44', 'name': 'Диссоциативные (конверсионные) расстройства', 'block': 'F40-F48', 'chapter': 'Диссоциативные расстройства'},
            {'code': 'F50', 'name': 'Расстройства приёма пищи', 'block': 'F50-F59', 'chapter': 'Поведенческие синдромы'},
            {'code': 'F60', 'name': 'Специфические расстройства личности', 'block': 'F60-F69', 'chapter': 'Расстройства личности и поведения в зрелом возрасте'},
            {'code': 'F70', 'name': 'Лёгкая умственная отсталость', 'block': 'F70-F79', 'chapter': 'Умственная отсталость'},
            {'code': 'F80', 'name': 'Специфические расстройства развития речи', 'block': 'F80-F89', 'chapter': 'Расстройства психологического развития'},
            {'code': 'F84', 'name': 'Расстройства аутистического спектра', 'block': 'F80-F89', 'chapter': 'Расстройства психологического развития'},
            {'code': 'F90', 'name': 'Расстройства активности и внимания (СДВГ)', 'block': 'F90-F98', 'chapter': 'Расстройства поведения'},
            {'code': 'F91', 'name': 'Расстройства поведения', 'block': 'F90-F98', 'chapter': 'Расстройства поведения'},
            {'code': 'F92', 'name': 'Расстройства эмоционального развития', 'block': 'F90-F98', 'chapter': 'Расстройства поведения'},
            {'code': 'F98', 'name': 'Другие расстройства поведения и эмоций', 'block': 'F90-F98', 'chapter': 'Расстройства поведения'},
        ]

        created_count = 0
        for d in diagnoses_data:
            _, created = Diagnosis.objects.get_or_create(
                code=d['code'],
                defaults={'name': d['name'], 'block': d['block'], 'chapter': d['chapter']}
            )
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f'Загружено {created_count} диагнозов МКБ-11'))

        departments_data = [
            {
                'name': 'Отделение шизофрении и психотических расстройств',
                'profile': 'F20-F29: Шизофрения, шизотипические и бредовые расстройства',
                'gender_restriction': 'ANY', 'age_category': 'ADULT',
                'total_beds': 40, 'occupied_beds': 0,
            },
            {
                'name': 'Отделение аффективных расстройств',
                'profile': 'F30-F39: Расстройства настроения',
                'gender_restriction': 'ANY', 'age_category': 'ADULT',
                'total_beds': 30, 'occupied_beds': 0,
            },
            {
                'name': 'Отделение тревожных и невротических расстройств',
                'profile': 'F40-F48: Тревожные, диссоциативные расстройства',
                'gender_restriction': 'ANY', 'age_category': 'ADULT',
                'total_beds': 25, 'occupied_beds': 0,
            },
            {
                'name': 'Отделение зависимостей',
                'profile': 'F10-F19: Психические расстройства, связанные с употреблением ПАВ',
                'gender_restriction': 'M', 'age_category': 'ADULT',
                'total_beds': 20, 'occupied_beds': 0,
            },
            {
                'name': 'Детско-подростковое отделение',
                'profile': 'F80-F98: Расстройства психологического развития, поведения',
                'gender_restriction': 'ANY', 'age_category': 'CHILD',
                'total_beds': 20, 'occupied_beds': 0,
            },
            {
                'name': 'Отделение интенсивной терапии',
                'profile': 'Крайне тяжёлые состояния любого профиля',
                'gender_restriction': 'ANY', 'age_category': 'ANY',
                'total_beds': 10, 'occupied_beds': 0,
            },
            {
                'name': 'Отделение личностных расстройств',
                'profile': 'F60: Специфические расстройства личности',
                'gender_restriction': 'F', 'age_category': 'ADULT',
                'total_beds': 15, 'occupied_beds': 0,
            },
        ]

        dept_created = 0
        for dd in departments_data:
            _, created = Department.objects.get_or_create(
                name=dd['name'],
                defaults={
                    'profile': dd['profile'],
                    'gender_restriction': dd['gender_restriction'],
                    'age_category': dd['age_category'],
                    'total_beds': dd['total_beds'],
                    'occupied_beds': dd['occupied_beds'],
                }
            )
            if created:
                dept_created += 1
        self.stdout.write(self.style.SUCCESS(f'Загружено {dept_created} отделений'))

        self.stdout.write(self.style.SUCCESS('Начальные данные успешно загружены!'))
