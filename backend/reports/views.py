"""
reports/views.py — Views REST para a API de relatórios.

Endpoints:
  POST   /api/reports/analyze/           → Análise com IA (principal)
  POST   /api/reports/upload/            → Upload de arquivo (CSV, Excel, PDF, etc.)
  POST   /api/reports/sheets/tabs/       → Lista abas de um Google Sheets
  GET    /api/reports/sheets/email/      → Retorna e-mail do Service Account
  GET    /api/reports/history/           → Histórico de relatórios (requer login)
  GET    /api/reports/history/<id>/      → Detalhe de um relatório
  DELETE /api/reports/history/<id>/      → Remove um relatório
"""

import logging

import pandas as pd
from django.core.files.base import ContentFile
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DataSource, Report, ChartImage
from .serializers import (
    AnalyzeRequestSerializer,
    DataSourceSerializer,
    GoogleSheetsTabsRequestSerializer,
    ReportSerializer,
)
from .services import google_sheets, file_parsers, ai_analysis, chart_generator

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# Upload de arquivo
# -------------------------------------------------------
class FileUploadView(APIView):
    """Recebe um arquivo (CSV, XLSX, XML, PDF, TXT) e salva como DataSource."""

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    # Mapeamento de extensão → source_type
    EXTENSION_MAP = {
        ".csv": "csv",
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".xml": "xml",
        ".pdf": "pdf",
        ".txt": "txt",
    }

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Nenhum arquivo enviado."}, status=status.HTTP_400_BAD_REQUEST)

        # Detecta tipo pelo nome do arquivo
        ext = "." + uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
        source_type = self.EXTENSION_MAP.get(ext)
        if source_type is None:
            return Response(
                {"detail": f"Extensão '{ext}' não suportada. Use: {', '.join(self.EXTENSION_MAP.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ds = DataSource.objects.create(
            user=request.user if request.user.is_authenticated else None,
            source_type=source_type,
            file=uploaded_file,
            name=request.data.get("name", uploaded_file.name),
        )

        return Response(DataSourceSerializer(ds).data, status=status.HTTP_201_CREATED)


# -------------------------------------------------------
# Google Sheets — listar abas
# -------------------------------------------------------
class GoogleSheetsTabsView(APIView):
    """Retorna a lista de abas de uma planilha Google Sheets."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleSheetsTabsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        url = serializer.validated_data["url"]
        try:
            tabs = google_sheets.list_tabs(url, user=request.user)
        except Exception as e:
            logger.error("Erro ao listar abas: %s", e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"tabs": tabs})


# -------------------------------------------------------
# Google Sheets — e-mail do Service Account
# -------------------------------------------------------
class GoogleSheetsEmailView(APIView):
    """Retorna o e-mail do Service Account para compartilhamento."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            email = google_sheets.get_service_account_email()
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"email": email})


# -------------------------------------------------------
# Análise principal com IA
# -------------------------------------------------------
class AnalyzeView(APIView):
    """Endpoint principal: recebe fontes + prompt, executa análise com IA.

    Aceita:
      - source_urls: links de Google Sheets
      - source_ids: IDs de DataSources já salvos (uploads anteriores)
      - files: arquivos enviados junto (multipart)
      - prompt: pergunta do usuário
      - generate_charts: bool
      - sheet_tabs: abas para cada URL
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        prompt = data["prompt"]
        generate_charts = data["generate_charts"]
        source_urls = data.get("source_urls", [])
        source_ids = data.get("source_ids", [])
        sheet_tabs = data.get("sheet_tabs", [])

        dataframes: list[pd.DataFrame] = []
        source_names: list[str] = []
        created_sources: list[DataSource] = []

        # 1) Carregar fontes do Google Sheets
        for i, url in enumerate(source_urls):
            tab = sheet_tabs[i] if i < len(sheet_tabs) else None
            try:
                df = google_sheets.read_tab_as_dataframe(url, tab_name=tab or None, user=request.user)
                dataframes.append(df)
                name = f"Google Sheets ({tab or 'aba principal'})"
                source_names.append(name)

                ds = DataSource.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    source_type="google_sheets",
                    url=url,
                    name=name,
                    sheet_tab=tab or "",
                )
                created_sources.append(ds)
            except Exception as e:
                logger.error("Erro ao carregar Google Sheets %s: %s", url, e)
                return Response(
                    {"detail": f"Erro ao acessar planilha: {e}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 2) Carregar DataSources já existentes (uploads anteriores)
        for ds_id in source_ids:
            try:
                ds = DataSource.objects.get(pk=ds_id)
                df = file_parsers.parse_file(ds.file.path, ds.source_type)
                dataframes.append(df)
                source_names.append(ds.name)
                created_sources.append(ds)
            except DataSource.DoesNotExist:
                return Response(
                    {"detail": f"Fonte de dados #{ds_id} não encontrada."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception as e:
                logger.error("Erro ao processar fonte #%d: %s", ds_id, e)
                return Response(
                    {"detail": f"Erro ao processar fonte #{ds_id}: {e}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 3) Carregar arquivos enviados diretamente nesta request
        for key in request.FILES:
            if key == "file" or key.startswith("file"):
                uploaded = request.FILES[key]
                ext = "." + uploaded.name.rsplit(".", 1)[-1].lower() if "." in uploaded.name else ""
                ext_map = FileUploadView.EXTENSION_MAP
                source_type = ext_map.get(ext)
                if source_type is None:
                    continue

                ds = DataSource.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    source_type=source_type,
                    file=uploaded,
                    name=uploaded.name,
                )
                try:
                    df = file_parsers.parse_file(ds.file.path, source_type)
                    dataframes.append(df)
                    source_names.append(uploaded.name)
                    created_sources.append(ds)
                except Exception as e:
                    logger.error("Erro ao processar arquivo %s: %s", uploaded.name, e)

        # Valida que temos pelo menos uma fonte
        if not dataframes:
            return Response(
                {"detail": "Nenhuma fonte de dados válida fornecida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4) Enviar para análise com IA (Groq)
        try:
            ai_result = ai_analysis.analyze(
                dataframes=dataframes,
                source_names=source_names,
                user_prompt=prompt,
            )
        except Exception as e:
            logger.error("Erro na análise com IA: %s", e)
            return Response(
                {"detail": f"Erro na análise com IA: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 5) Salvar relatório
        report = Report.objects.create(
            user=request.user if request.user.is_authenticated else None,
            prompt=prompt,
            result=ai_result["analysis"],
        )
        report.data_sources.set(created_sources)

        # 6) Gerar gráficos se solicitado
        chart_data = []
        if generate_charts and ai_result["chart_configs"]:
            chart_results = chart_generator.generate_charts_from_configs(
                dataframes=dataframes,
                chart_configs=ai_result["chart_configs"],
            )
            for cr in chart_results:
                if "error" in cr:
                    chart_data.append({"error": cr["error"], "title": cr["title"]})
                    continue

                chart_obj = ChartImage.objects.create(
                    report=report,
                    title=cr["title"],
                    chart_config=ai_result["chart_configs"][chart_results.index(cr)]
                    if chart_results.index(cr) < len(ai_result["chart_configs"])
                    else {},
                )
                # Salva a imagem no campo ImageField
                chart_obj.image.save(
                    f"{cr['file_path'].split('/')[-1]}",
                    ContentFile(cr["image_bytes"]),
                    save=True,
                )
                chart_data.append({
                    "id": chart_obj.id,
                    "title": cr["title"],
                    "image_url": chart_obj.image.url,
                })

        # 7) Resposta final
        return Response({
            "report": ReportSerializer(report).data,
            "charts": chart_data,
            "ai_usage": ai_result.get("usage", {}),
        }, status=status.HTTP_201_CREATED)


# -------------------------------------------------------
# Histórico de relatórios (requer autenticação)
# -------------------------------------------------------
class ReportHistoryListView(generics.ListAPIView):
    """Lista relatórios do usuário autenticado."""

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)


class ReportHistoryDetailView(generics.RetrieveDestroyAPIView):
    """Detalhes ou exclusão de um relatório do usuário."""

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)
