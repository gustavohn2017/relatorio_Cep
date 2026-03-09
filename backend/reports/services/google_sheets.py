"""
reports/services/google_sheets.py — Integração com Google Sheets.

Funcionalidades:
  • Autenticar via Service Account ou credenciais OAuth do usuário
  • Listar abas de uma planilha
  • Ler todos os dados de uma aba como DataFrame Pandas

Fluxo de permissão:
  A) Usuário logado via Google → usa as credenciais OAuth do usuário
     para acessar planilhas que ele já tem permissão (sem precisar
     compartilhar com o Service Account).
  B) Sem credenciais OAuth → fallback para Service Account.
     O usuário deve compartilhar a planilha com o e-mail do SA.
"""

import re
import logging

import gspread
import pandas as pd
from django.conf import settings
from google.oauth2.credentials import Credentials as OAuthCredentials

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Cache da conexão SA (singleton leve por processo)
# -------------------------------------------------------
_sa_client: gspread.Client | None = None


def _get_sa_client() -> gspread.Client:
    """Retorna um client gspread autenticado via Service Account."""
    global _sa_client
    if _sa_client is None:
        _sa_client = gspread.service_account(filename=settings.GOOGLE_CREDENTIALS_FILE)
        logger.info("Google Sheets client (SA) autenticado com sucesso.")
    return _sa_client


def _get_user_client(user) -> gspread.Client | None:
    """Tenta criar um client gspread com as credenciais Google OAuth do
    usuário. Retorna None se o usuário não tiver conta Google vinculada."""
    if user is None or not user.is_authenticated:
        return None

    from accounts.models import SocialAccount

    try:
        social = SocialAccount.objects.get(user=user, provider="google")
    except SocialAccount.DoesNotExist:
        return None

    if not social.access_token:
        return None

    creds = OAuthCredentials(
        token=social.access_token,
        refresh_token=social.refresh_token or None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )

    try:
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.warning("Falha ao autorizar com credenciais do usuário: %s", e)
        return None


def _get_client(user=None) -> gspread.Client:
    """Retorna o melhor client disponível: do usuário (se Google OAuth)
    ou fallback para Service Account."""
    client = _get_user_client(user)
    if client is not None:
        return client
    return _get_sa_client()


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
    client = _get_sa_client()
    return client.auth.service_account_email


def list_tabs(url: str, user=None) -> list[dict]:
    """Lista todas as abas (worksheets) de uma planilha.

    Retorna lista de dicts: [{"title": "Sheet1", "rows": 1000, "cols": 26}, ...]
    """
    client = _get_client(user)
    spreadsheet_id = _extract_spreadsheet_id(url)
    spreadsheet = client.open_by_key(spreadsheet_id)
    return [
        {"title": ws.title, "rows": ws.row_count, "cols": ws.col_count}
        for ws in spreadsheet.worksheets()
    ]


def read_tab_as_dataframe(url: str, tab_name: str | None = None, user=None) -> pd.DataFrame:
    """Lê uma aba da planilha e retorna como DataFrame.

    Se tab_name for None, lê a primeira aba.
    Usa credenciais do usuário se disponíveis, senão Service Account.
    """
    client = _get_client(user)
    spreadsheet_id = _extract_spreadsheet_id(url)
    spreadsheet = client.open_by_key(spreadsheet_id)

    if tab_name:
        worksheet = spreadsheet.worksheet(tab_name)
    else:
        worksheet = spreadsheet.sheet1

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
