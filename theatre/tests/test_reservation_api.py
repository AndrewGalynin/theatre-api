from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Performance, Play, Reservation, TheatreHall, Ticket

RESERVATION_URL = reverse("theatre:reservation-list")


def sample_performance():
    play = Play.objects.create(title="Hamlet", description="Tragedy")
    hall = TheatreHall.objects.create(
        name="Chamber Hall", rows=5, seats_in_row=8
    )
    return Performance.objects.create(
        play=play,
        theatre_hall=hall,
        show_time=datetime(2026, 11, 22, 18, 30, tzinfo=timezone.utc),
    )


class UnauthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "viewer@theatre.com",
            "testpass123",
        )
        self.other_user = get_user_model().objects.create_user(
            "other@theatre.com",
            "testpass123",
        )
        self.client.force_authenticate(self.user)
        self.performance = sample_performance()

    def test_list_reservations_only_own(self):
        Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=self.other_user)

        res = self.client.get(RESERVATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_create_reservation_with_tickets_success(self):
        payload = {
            "tickets": [
                {"row": 1, "seat": 2, "performance": self.performance.id},
                {"row": 1, "seat": 3, "performance": self.performance.id},
            ]
        }
        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_create_reservation_invalid_row_error(self):
        payload = {
            "tickets": [
                {"row": 99, "seat": 2, "performance": self.performance.id},
            ]
        }
        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_create_reservation_duplicate_seat_error(self):
        existing_res = Reservation.objects.create(user=self.other_user)
        Ticket.objects.create(
            row=2,
            seat=4,
            performance=self.performance,
            reservation=existing_res,
        )

        payload = {
            "tickets": [
                {"row": 2, "seat": 4, "performance": self.performance.id},
            ]
        }
        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.filter(user=self.user).count(), 0)
