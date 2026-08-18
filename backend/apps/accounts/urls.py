"""User and role management routes under ``/api/``."""
from __future__ import annotations

from typing import List, Union

from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .views import RoleViewSet, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")

urlpatterns: List[Union[URLResolver, URLPattern]] = [
    path("", include(router.urls)),
]
