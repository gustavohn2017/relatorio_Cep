"""
reports/serializers.py — Serializadores REST para fontes de dados, relatórios e gráficos.
"""

from rest_framework import serializers
from .models import DataSource, Report, ChartImage


class DataSourceSerializer(serializers.ModelSerializer):
    """Serializa DataSource para criação e listagem."""

    class Meta:
        model = DataSource
        fields = (
            "id", "source_type", "url", "file", "name",
            "sheet_tab", "created_at",
        )
        read_only_fields = ("id", "created_at")


class ChartImageSerializer(serializers.ModelSerializer):
    """Serializa gráficos gerados."""

    class Meta:
        model = ChartImage
        fields = ("id", "title", "image", "chart_config", "created_at")
        read_only_fields = ("id", "created_at")


class ReportSerializer(serializers.ModelSerializer):
    """Serializa relatório com fontes de dados e gráficos."""

    data_sources = DataSourceSerializer(many=True, read_only=True)
    charts = ChartImageSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = (
            "id", "prompt", "result", "data_sources",
            "charts", "created_at",
        )
        read_only_fields = ("id", "result", "created_at")


class AnalyzeRequestSerializer(serializers.Serializer):
    """Validação do payload de análise enviado pelo frontend.

    O usuário pode enviar:
      - sources: lista de fontes (links Google Sheets ou IDs de DataSource)
      - files: arquivos enviados via multipart
      - prompt: a pergunta/instrução para a IA
      - generate_charts: se deve gerar gráficos
    """

    prompt = serializers.CharField(max_length=5000)
    generate_charts = serializers.BooleanField(default=False)

    # Fontes via link (Google Sheets) ou IDs de fontes já salvas
    source_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
    )
    source_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
    # Abas específicas para cada URL (mesmo índice)
    sheet_tabs = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        default=list,
    )


class GoogleSheetsTabsRequestSerializer(serializers.Serializer):
    """Validação para consulta de abas de uma planilha Google Sheets."""
    url = serializers.URLField()
