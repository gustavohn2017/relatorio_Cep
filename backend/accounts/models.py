"""
accounts/models.py — Modelos de perfil e contas sociais.

Utiliza o modelo de usuário padrão do Django.
Profile armazena dados complementares.
SocialAccount armazena credenciais OAuth para login social e
acesso a serviços externos (ex.: Google Sheets).
"""

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Dados extras associados a um User do Django."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"Perfil de {self.user.username}"


class SocialAccount(models.Model):
    """Credenciais OAuth vinculadas a um usuário."""

    PROVIDER_CHOICES = [
        ("google", "Google"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_uid = models.CharField(max_length=255)
    email = models.EmailField()
    access_token = models.TextField(blank=True, default="")
    refresh_token = models.TextField(blank=True, default="")
    token_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("provider", "provider_uid")
        verbose_name = "Conta Social"
        verbose_name_plural = "Contas Sociais"

    def __str__(self):
        return f"{self.get_provider_display()} — {self.email}"
