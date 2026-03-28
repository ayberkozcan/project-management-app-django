from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account


class AuthRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = Account.objects.create_user(
            email="owner@example.com",
            username="owner",
            password="testpass123",
            first_name="Owner",
            last_name="User",
        )

    def test_login_is_rate_limited_after_five_posts_per_minute(self):
        url = reverse("login")

        for _ in range(5):
            response = self.client.post(
                url,
                {"username": self.user.email, "password": "wrong-password"},
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            url,
            {"username": self.user.email, "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 429)
