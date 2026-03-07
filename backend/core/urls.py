"""
core/urls.py — Roteamento principal do projeto.

Centraliza as rotas da API REST e do painel admin.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Painel administrativo do Django
    path("admin/", admin.site.urls),
    # API de autenticação e contas
    path("api/auth/", include("accounts.urls")),
    # API de relatórios, upload, análise e gráficos
    path("api/reports/", include("reports.urls")),
]
