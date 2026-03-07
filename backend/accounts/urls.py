"""
accounts/urls.py — Rotas do app de autenticação.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    # Registro
    path("register/", views.RegisterView.as_view(), name="register"),
    # JWT login / refresh
    path("token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Perfil do usuário logado
    path("me/", views.MeView.as_view(), name="me"),
    # Recuperação de senha
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
