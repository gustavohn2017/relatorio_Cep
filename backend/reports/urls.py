"""
reports/urls.py — Rotas da API de relatórios.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Análise principal com IA
    path("analyze/", views.AnalyzeView.as_view(), name="analyze"),
    # Upload de arquivo
    path("upload/", views.FileUploadView.as_view(), name="file_upload"),
    # Google Sheets
    path("sheets/tabs/", views.GoogleSheetsTabsView.as_view(), name="sheets_tabs"),
    path("sheets/email/", views.GoogleSheetsEmailView.as_view(), name="sheets_email"),
    # Histórico (autenticado)
    path("history/", views.ReportHistoryListView.as_view(), name="report_history"),
    path("history/<int:pk>/", views.ReportHistoryDetailView.as_view(), name="report_detail"),
]
