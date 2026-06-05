from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthenticationAPITests(APITestCase):
    def test_signup_creates_user_and_returns_tokens(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'clinton',
                'email': 'clinton@example.com',
                'password': 'StrongPass123!',
                'password_confirm': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['user']['email'], 'clinton@example.com')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(
            username='first',
            email='same@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('signup'),
            {
                'username': 'second',
                'email': 'same@example.com',
                'password': 'StrongPass123!',
                'password_confirm': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_signup_rejects_duplicate_username(self):
        User.objects.create_user(
            username='taken',
            email='taken@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('signup'),
            {
                'username': 'taken',
                'email': 'new@example.com',
                'password': 'StrongPass123!',
                'password_confirm': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'clinton',
                'email': 'clinton@example.com',
                'password': 'StrongPass123!',
                'password_confirm': 'DifferentPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_login_returns_tokens_for_valid_credentials(self):
        User.objects.create_user(
            username='clinton',
            email='clinton@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'clinton', 'password': 'StrongPass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'clinton')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_login_rejects_invalid_credentials(self):
        User.objects.create_user(
            username='clinton',
            email='clinton@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'clinton', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_returns_access_token(self):
        signup_response = self.client.post(
            reverse('signup'),
            {
                'username': 'clinton',
                'email': 'clinton@example.com',
                'password': 'StrongPass123!',
                'password_confirm': 'StrongPass123!',
            },
            format='json',
        )
        refresh_token = signup_response.data['tokens']['refresh']

        response = self.client.post(
            reverse('token-refresh'),
            {'refresh': refresh_token},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_retrieve_profile(self):
        user = User.objects.create_user(
            username='clinton',
            email='clinton@example.com',
            password='StrongPass123!',
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'clinton')
        self.assertEqual(response.data['email'], 'clinton@example.com')

    def test_authenticated_user_can_update_profile(self):
        user = User.objects.create_user(
            username='clinton',
            email='clinton@example.com',
            password='StrongPass123!',
        )
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            reverse('profile'),
            {
                'first_name': 'Clinton',
                'last_name': 'Codes',
                'email': 'updated@example.com',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Clinton')
        self.assertEqual(user.last_name, 'Codes')
        self.assertEqual(user.email, 'updated@example.com')

    def test_profile_update_rejects_duplicate_email(self):
        User.objects.create_user(
            username='other',
            email='other@example.com',
            password='StrongPass123!',
        )
        user = User.objects.create_user(
            username='clinton',
            email='clinton@example.com',
            password='StrongPass123!',
        )
        self.client.force_authenticate(user=user)

        response = self.client.patch(
            reverse('profile'),
            {'email': 'other@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
