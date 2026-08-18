"""Root URL routing for the Ledger de Certificados.

Mounts the Django admin, the OpenAPI schema (drf-spectacular) and the API
routes under the ``/api`` prefix.

* ``/api/auth/``          — login (TokenObtainPair), refresh, logout, me.
* ``/api/users/``         — user CRUD (Admin only), ``/api/roles/``.
* ``/api/ledger/``        — certificates (list, create, sign, supersede).
"""
from __future__ import annotations

from typing import List, Union

from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns: List[Union[URLResolver, URLPattern]] = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls_auth")),
    path("api/", include("apps.accounts.urls")),
    path("api/ledger/", include("apps.ledger.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
