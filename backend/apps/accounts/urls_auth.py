"""Authentication routes under ``/api/auth/``."""
from __future__ import annotations

from typing import List

from django.urls import URLPattern, path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, MeView

urlpatterns: List[URLPattern] = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
]
