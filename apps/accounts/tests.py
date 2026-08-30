from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

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


class AuthenticationAPITests(APITestCase):
    def test_register_success(self):
        url = reverse('accounts:register')

        data = {
            'email': 'test_register@gmail.com',
            'password': 'StrongPass123!',
        }

        response = self.client.post(
            url,
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            CustomUser.objects.filter(
                email=data['email']
            ).exists()
        )

        user = CustomUser.objects.get(
            email=data['email']
        )

        self.assertTrue(
            user.check_password(data['password'])
        )

    def test_register_duplicate_email(self):
        email = 'duplicate@gmail.com'
        password = 'StrongPass123!'

        CustomUser.objects.create_user(
            email=email,
            password=password,
        )

        url = reverse('accounts:register')

        data = {
            'email': email,
            'password': 'strongPass123!',
        }

        response = self.client.post(
            url,
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            CustomUser.objects.filter(email=email).count(),
            1,
        )

    def test_login_success(self):
        email = 'login@gmail.com'
        password = 'StrongPass123!'

        CustomUser.objects.create_user(
            email=email,
            password=password,
        )

        url = reverse('accounts:token_obtain_pair')

        data = {
            'email': email,
            'password': password,
        }

        response = self.client.post(
            url,
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            'access',
            response.data,
        )

        self.assertIn(
            'refresh',
            response.data,
        )

    def test_login_wrong_password(self):
        email = 'login_wrong@gmail.com'
        password = 'StrongPass123!'

        CustomUser.objects.create_user(
            email=email,
            password=password,
        )

        url = reverse('accounts:token_obtain_pair')

        data = {
            'email': email,
            'password': 'WrongPass123!',
        }

        response = self.client.post(
            url,
            data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertNotIn(
            'access',
            response.data,
        )

        self.assertNotIn(
            'refresh',
            response.data,
        )

    def test_refresh_token_success(self):
        email = 'refresh@gmail.com'
        password = 'StrongPass123!'

        CustomUser.objects.create_user(
            email=email,
            password=password,
        )

        login_url = reverse('accounts:token_obtain_pair')

        login_response = self.client.post(
            login_url,
            {
                'email': email,
                'password': password,
            },
            format='json',
        )

        refresh_token = login_response.data['refresh']

        refresh_url = reverse('accounts:token_refresh')

        response = self.client.post(
            refresh_url,
            {
                'refresh': refresh_token,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            'access',
            response.data,
        )