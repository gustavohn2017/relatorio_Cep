"""
reports/models.py — Modelos de dados para relatórios.

DataSource  → cada fonte de dados enviada pelo usuário (link ou upload)
Report      → resultado da análise gerada pela IA
ChartImage  → gráficos gerados e salvos como imagem
"""

from django.conf import settings
from django.db import models


class DataSource(models.Model):
    """Representa uma fonte de dados — link do Google Sheets ou arquivo enviado."""

    SOURCE_TYPE_CHOICES = [
        ("google_sheets", "Google Sheets"),
        ("csv", "CSV"),
        ("xlsx", "Excel (XLSX)"),
        ("xml", "XML"),
        ("pdf", "PDF"),
        ("txt", "Texto"),
    ]

    # Usuário que enviou (pode ser nulo para uso anônimo)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="data_sources",
    )
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    # URL (para Google Sheets) ou caminho do arquivo (para uploads)
    url = models.URLField(max_length=500, blank=True)
    file = models.FileField(upload_to="uploads/%Y/%m/", blank=True, null=True)
    # Nome amigável dado pelo usuário
    name = models.CharField(max_length=255, blank=True)
    # Aba específica do Google Sheets (ex: "Sheet1")
    sheet_tab = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fonte de Dados"
        verbose_name_plural = "Fontes de Dados"

    def __str__(self):
        return self.name or f"{self.source_type} – {self.pk}"


class Report(models.Model):
    """Resultado gerado pela IA a partir de uma ou mais fontes de dados."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    # Pergunta/prompt do usuário
    prompt = models.TextField()
    # Resposta da IA (Markdown)
    result = models.TextField(blank=True)
    # Fontes usadas
    data_sources = models.ManyToManyField(DataSource, related_name="reports")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"

    def __str__(self):
        return f"Relatório #{self.pk} — {self.prompt[:60]}"


class ChartImage(models.Model):
    """Gráfico gerado a partir dos dados de um relatório."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="charts")
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="charts/%Y/%m/")
    chart_config = models.JSONField(default=dict, blank=True, help_text="Configuração Plotly/Matplotlib serializada")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gráfico"
        verbose_name_plural = "Gráficos"

    def __str__(self):
        return self.title or f"Gráfico #{self.pk}"
