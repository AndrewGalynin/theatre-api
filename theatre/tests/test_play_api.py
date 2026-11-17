import os
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Actor, Genre, Play
from theatre.serializers import PlayDetailSerializer, PlayListSerializer

PLAY_URL = reverse("theatre:play-list")


def sample_play(**params):
    defaults = {
        "title": "Sample play",
        "description": "Sample description",
    }
    defaults.update(params)
    return Play.objects.create(**defaults)


def sample_genre(**params):
    defaults = {"name": "Drama"}
    defaults.update(params)
    return Genre.objects.create(**defaults)


def sample_actor(**params):
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(params)
    return Actor.objects.create(**defaults)


def image_upload_url(play_id):
    return reverse("theatre:play-upload-image", args=[play_id])


def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


class UnauthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(PLAY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@theatre.com",
            "testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_list_plays(self):
        sample_play()
        play_with_relations = sample_play(title="Hamlet")
        genre = sample_genre()
        actor = sample_actor()
        play_with_relations.genres.add(genre)
        play_with_relations.actors.add(actor)

        res = self.client.get(PLAY_URL)

        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_plays_by_title(self):
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="Macbeth")

        res = self.client.get(PLAY_URL, {"title": "hamlet"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_plays_by_genres(self):
        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        play3 = sample_play(title="Play without genres")

        genre1 = sample_genre(name="Comedy")
        genre2 = sample_genre(name="Tragedy")

        play1.genres.add(genre1)
        play2.genres.add(genre2)

        res = self.client.get(PLAY_URL, {"genres": f"{genre1.id},{genre2.id}"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)
        serializer3 = PlayListSerializer(play3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_plays_by_invalid_genres_returns_400(self):
        res = self.client.get(PLAY_URL, {"genres": "abc"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_plays_by_actors(self):
        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")

        actor1 = sample_actor(first_name="Benedict", last_name="Cumberbatch")
        actor2 = sample_actor(first_name="Andrew", last_name="Scott")

        play1.actors.add(actor1)
        play2.actors.add(actor2)

        res = self.client.get(PLAY_URL, {"actors": f"{actor1.id}"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_play_detail(self):
        play = sample_play()
        play.genres.add(sample_genre())
        play.actors.add(sample_actor())

        url = detail_url(play.id)
        res = self.client.get(url)

        serializer = PlayDetailSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_play_forbidden(self):
        payload = {
            "title": "Forbidden Play",
            "description": "Should not be created",
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@theatre.com",
            "testpass123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_play(self):
        genre = sample_genre()
        actor = sample_actor()
        payload = {
            "title": "Othello",
            "description": "Shakespeare tragedy",
            "genres": [genre.id],
            "actors": [actor.id],
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.title, payload["title"])
        self.assertIn(genre, play.genres.all())
        self.assertIn(actor, play.actors.all())

    def test_delete_play_allowed(self):
        play = sample_play()
        url = detail_url(play.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Play.objects.filter(id=play.id).exists())


class PlayImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@theatre.com",
            "password123",
        )
        self.client.force_authenticate(self.user)
        self.play = sample_play()

    def tearDown(self):
        self.play.image.delete()

    def test_upload_image_to_play(self):
        url = image_upload_url(self.play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.play.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.play.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.play.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
