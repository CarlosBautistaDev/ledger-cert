"""Certificate routes under ``/api/ledger/``."""
from __future__ import annotations

from typing import List, Union

from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from .views import CertificateViewSet

router = DefaultRouter()
router.register("certificates", CertificateViewSet, basename="certificate")

urlpatterns: List[Union[URLResolver, URLPattern]] = [
    path("", include(router.urls)),
]
