"""
accounts/models.py — Modelo de perfil de usuário.

Utiliza o modelo de usuário padrão do Django (AbstractUser não é
necessário neste momento). O perfil armazena dados complementares.
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
