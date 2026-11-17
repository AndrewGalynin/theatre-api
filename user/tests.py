from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
MANAGE_USER_URL = reverse("user:manage")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UnauthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        payload = {
            "email": "test@theatre.com",
            "password": "testpassword123",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_with_email_exists_error(self):
        payload = {
            "email": "test@theatre.com",
            "password": "testpassword123",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        payload = {
            "email": "test@theatre.com",
            "password": "123",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload["email"]
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        user_details = {
            "email": "test@theatre.com",
            "password": "testpassword123",
        }
        create_user(**user_details)

        res = self.client.post(TOKEN_URL, user_details)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="viewer@theatre.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)
        self.assertFalse(res.data["is_staff"])

    def test_post_me_not_allowed(self):
        res = self.client.post(MANAGE_USER_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {"password": "newstrongpassword123"}
        res = self.client.patch(MANAGE_USER_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(payload["password"]))
