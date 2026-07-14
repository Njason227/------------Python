from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123',
            first_name='Тест', last_name='Пользователь',
            role='doctor'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin', password='admin123',
            role='admin'
        )

    def test_user_str(self):
        self.assertEqual(str(self.user), 'Тест Пользователь (Врач приёмного отделения)')

    def test_user_role_properties(self):
        self.assertTrue(self.user.is_doctor)
        self.assertFalse(self.user.is_admin_role)
        self.assertFalse(self.user.is_senior_nurse)

    def test_admin_role_properties(self):
        self.assertTrue(self.admin_user.is_admin_role)


class AuthViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123',
            role='doctor'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser', 'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    def test_register_requires_admin(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_register(self):
        admin = User.objects.create_superuser(
            username='admin', password='admin123', role='admin'
        )
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)

    def test_user_list_requires_admin(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 302)
