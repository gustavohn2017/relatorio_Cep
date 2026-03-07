"""
reports/services/file_parsers.py — Parsers para diferentes formatos de arquivo.

Cada função recebe o caminho do arquivo e retorna um DataFrame Pandas.
Projetado para planilhas de larga escala com muitas informações.
"""

import logging

import pandas as pd
import pdfplumber
from lxml import etree

logger = logging.getLogger(__name__)


def parse_csv(filepath: str) -> pd.DataFrame:
    """Lê CSV com detecção automática de delimitador.
    Usa low_memory=False para arquivos grandes e evitar dtype warnings.
    """
    df = pd.read_csv(filepath, low_memory=False, encoding="utf-8", on_bad_lines="skip")
    logger.info("CSV carregado: %d linhas × %d colunas", len(df), len(df.columns))
    return df


def parse_excel(filepath: str, sheet_name: str | None = None) -> pd.DataFrame:
    """Lê planilha Excel (.xlsx / .xls).
    Se sheet_name=None, lê a primeira aba.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name or 0, engine="openpyxl")
    logger.info("Excel carregado: %d linhas × %d colunas", len(df), len(df.columns))
    return df


def parse_xml(filepath: str) -> pd.DataFrame:
    """Converte XML tabular em DataFrame.
    Espera elementos filhos repetidos do root como linhas.
    Cada sub-elemento vira uma coluna.
    """
    tree = etree.parse(filepath)  # noqa: S320 — arquivo local confiável
    root = tree.getroot()

    rows = []
    for child in root:
        row = {}
        for element in child:
            # Remove namespace do tag, se houver
            tag = etree.QName(element.tag).localname if "}" in element.tag else element.tag
            row[tag] = element.text
        rows.append(row)

    df = pd.DataFrame(rows)
    logger.info("XML carregado: %d linhas × %d colunas", len(df), len(df.columns))
    return df


def parse_pdf(filepath: str) -> pd.DataFrame:
    """Extrai tabelas de todas as páginas de um PDF.
    Concatena todas as tabelas encontradas em um único DataFrame.
    """
    all_tables: list[pd.DataFrame] = []

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                # Primeira linha como cabeçalho
                header = table[0]
                data = table[1:]
                df_table = pd.DataFrame(data, columns=header)
                all_tables.append(df_table)
                logger.debug("PDF página %d: tabela com %d linhas", page_num, len(data))

    if not all_tables:
        # Fallback: extrair texto bruto linha a linha
        logger.warning("Nenhuma tabela encontrada no PDF. Extraindo texto bruto.")
        lines: list[str] = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))
        df = pd.DataFrame({"texto": lines})
    else:
        df = pd.concat(all_tables, ignore_index=True)

    logger.info("PDF carregado: %d linhas × %d colunas", len(df), len(df.columns))
    return df


def parse_txt(filepath: str) -> pd.DataFrame:
    """Lê arquivo de texto. Tenta tab-separated primeiro; se falhar, lê linhas brutas."""
    try:
        df = pd.read_csv(filepath, sep="\t", low_memory=False, encoding="utf-8")
        if len(df.columns) > 1:
            logger.info("TXT (tab-separated) carregado: %d linhas × %d colunas", len(df), len(df.columns))
            return df
    except Exception:
        pass

    # Fallback: cada linha como uma entrada
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    df = pd.DataFrame({"texto": [line.strip() for line in lines if line.strip()]})
    logger.info("TXT (linhas) carregado: %d linhas", len(df))
    return df


# -------------------------------------------------------
# Mapeamento tipo → parser
# -------------------------------------------------------
PARSERS = {
    "csv": parse_csv,
    "xlsx": parse_excel,
    "xml": parse_xml,
    "pdf": parse_pdf,
    "txt": parse_txt,
}


def parse_file(filepath: str, source_type: str, **kwargs) -> pd.DataFrame:
    """Função de entrada unificada: seleciona o parser correto pelo tipo."""
    parser = PARSERS.get(source_type)
    if parser is None:
        raise ValueError(f"Tipo de arquivo não suportado: {source_type}")
    return parser(filepath, **kwargs)
