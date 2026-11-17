from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Performance, Play, Reservation, TheatreHall, Ticket

PERFORMANCE_URL = reverse("theatre:performance-list")


def sample_theatre_hall(**params):
    defaults = {
        "name": "Main Stage",
        "rows": 10,
        "seats_in_row": 10,
    }
    defaults.update(params)
    return TheatreHall.objects.create(**defaults)


def sample_play(**params):
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)
    return Play.objects.create(**defaults)


def sample_performance(**params):
    play = params.pop("play", None) or sample_play()
    hall = params.pop("theatre_hall", None) or sample_theatre_hall()
    defaults = {
        "play": play,
        "theatre_hall": hall,
        "show_time": datetime(2026, 11, 20, 19, 0, tzinfo=timezone.utc),
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


def detail_url(performance_id):
    return reverse("theatre:performance-detail", args=[performance_id])


class UnauthenticatedPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PERFORMANCE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "viewer@theatre.com",
            "testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_list_performances_with_tickets_available(self):
        performance = sample_performance()
        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=1, seat=1, performance=performance, reservation=reservation
        )

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]["tickets_available"], 99)

    def test_filter_performances_by_date(self):
        perf1 = sample_performance(
            show_time=datetime(2026, 11, 20, 19, 0, tzinfo=timezone.utc)
        )
        perf2 = sample_performance(
            show_time=datetime(2026, 11, 25, 19, 0, tzinfo=timezone.utc)
        )

        res = self.client.get(PERFORMANCE_URL, {"date": "2026-11-20"})

        ids = [item["id"] for item in res.data]
        self.assertIn(perf1.id, ids)
        self.assertNotIn(perf2.id, ids)

    def test_filter_performances_by_play(self):
        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        perf1 = sample_performance(play=play1)
        perf2 = sample_performance(play=play2)

        res = self.client.get(PERFORMANCE_URL, {"play": play1.id})

        ids = [item["id"] for item in res.data]
        self.assertIn(perf1.id, ids)
        self.assertNotIn(perf2.id, ids)

    def test_retrieve_performance_detail_with_taken_places(self):
        performance = sample_performance()
        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=2, seat=5, performance=performance, reservation=reservation
        )

        res = self.client.get(detail_url(performance.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["taken_places"], [{"row": 2, "seat": 5}])

    def test_create_performance_forbidden(self):
        play = sample_play()
        hall = sample_theatre_hall()
        payload = {
            "play": play.id,
            "theatre_hall": hall.id,
            "show_time": "2026-12-01T19:00:00Z",
        }
        res = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
