from django.test import TestCase

from .models import CustomUser


class CustomUserTests(TestCase):

    def test_create_user_with_email(self):
        email = 'test_user@gmail.com'
        password = 'StrongPass123!'

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                email='',
                password='StrongPass123!',
            )

    def test_create_superuser(self):
        email = 'admin@gmail.com'
        password = 'StrongPass123!'

        user = CustomUser.objects.create_superuser(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)