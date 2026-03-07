"""
reports/services/google_sheets.py — Integração com Google Sheets.

Funcionalidades:
  • Autenticar usando Service Account
  • Listar abas de uma planilha
  • Ler todos os dados de uma aba como DataFrame Pandas
  • Suporte a planilhas restritas (basta compartilhar com o e-mail
    do Service Account)

Fluxo de permissão simplificado:
  1. O admin cria um Service Account no Google Cloud Console.
  2. Baixa o JSON de credenciais e coloca em credentials/.
  3. O usuário compartilha a planilha com o e-mail do Service Account
     (ex: relatorio@projeto.iam.gserviceaccount.com).
  4. A aplicação acessa a planilha normalmente via API.
"""

import re
import logging

import gspread
import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Cache da conexão (singleton leve por processo)
# -------------------------------------------------------
_client: gspread.Client | None = None


def _get_client() -> gspread.Client:
    """Retorna um client gspread autenticado via Service Account."""
    global _client
    if _client is None:
        _client = gspread.service_account(filename=settings.GOOGLE_CREDENTIALS_FILE)
        logger.info("Google Sheets client autenticado com sucesso.")
    return _client


def _extract_spreadsheet_id(url: str) -> str:
    """Extrai o ID da planilha a partir de uma URL do Google Sheets."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(f"URL inválida para Google Sheets: {url}")
    return match.group(1)


# -------------------------------------------------------
# API pública
# -------------------------------------------------------


def get_service_account_email() -> str:
    """Retorna o e-mail do Service Account para que o usuário saiba
    com quem compartilhar a planilha."""
    client = _get_client()
    return client.auth.service_account_email


def list_tabs(url: str) -> list[dict]:
    """Lista todas as abas (worksheets) de uma planilha.

    Retorna lista de dicts: [{"title": "Sheet1", "rows": 1000, "cols": 26}, ...]
    """
    client = _get_client()
    spreadsheet_id = _extract_spreadsheet_id(url)
    spreadsheet = client.open_by_key(spreadsheet_id)
    return [
        {"title": ws.title, "rows": ws.row_count, "cols": ws.col_count}
        for ws in spreadsheet.worksheets()
    ]


def read_tab_as_dataframe(url: str, tab_name: str | None = None) -> pd.DataFrame:
    """Lê uma aba da planilha e retorna como DataFrame.

    Se tab_name for None, lê a primeira aba.
    Otimizado para planilhas grandes: usa get_all_records() que
    faz uma única requisição batch.
    """
    client = _get_client()
    spreadsheet_id = _extract_spreadsheet_id(url)
    spreadsheet = client.open_by_key(spreadsheet_id)

    if tab_name:
        worksheet = spreadsheet.worksheet(tab_name)
    else:
        worksheet = spreadsheet.sheet1

    # get_all_records retorna lista de dicts, eficiente para larga escala
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    logger.info(
        "Google Sheets '%s' aba '%s': %d linhas × %d colunas carregadas.",
        spreadsheet_id,
        worksheet.title,
        len(df),
        len(df.columns),
    )
    return df
