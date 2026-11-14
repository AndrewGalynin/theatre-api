from django.urls import include, path
from rest_framework import routers

from theatre.views import (
    ActorViewSet,
    GenreViewSet,
    TheatreHallViewSet,
)

router = routers.DefaultRouter()
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("theatre-halls", TheatreHallViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "theatre"
