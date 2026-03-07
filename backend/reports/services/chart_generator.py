"""
reports/services/chart_generator.py — Geração de gráficos com Plotly.

Recebe configurações de gráficos (vindas da IA ou do usuário) e os
dados em DataFrame, e gera imagens PNG de alta qualidade.

Suporta: bar, line, pie, scatter, histogram, heatmap.
"""

import io
import logging
import uuid
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.conf import settings

logger = logging.getLogger(__name__)

# Diretório para salvar gráficos
CHARTS_DIR = Path(settings.MEDIA_ROOT) / "charts"


def _ensure_charts_dir():
    """Cria o diretório de gráficos se não existir."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def _apply_aggregation(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Aplica agrupamento e agregação conforme configuração."""
    group_by = config.get("group_by")
    aggregation = config.get("aggregation")
    y = config.get("y")

    if not group_by or not aggregation:
        return df

    if isinstance(y, list):
        cols = y
    else:
        cols = [y] if y else []

    agg_funcs = {col: aggregation for col in cols if col in df.columns}
    if not agg_funcs:
        return df

    # Converte colunas para numérico quando possível
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.groupby(group_by, as_index=False).agg(agg_funcs)


# -------------------------------------------------------
# Geradores por tipo de gráfico
# -------------------------------------------------------

def _bar_chart(df: pd.DataFrame, config: dict) -> go.Figure:
    x = config.get("x")
    y = config.get("y")
    title = config.get("title", "Gráfico de Barras")
    if isinstance(y, list):
        fig = go.Figure()
        for col in y:
            if col in df.columns:
                fig.add_trace(go.Bar(x=df[x], y=pd.to_numeric(df[col], errors="coerce"), name=col))
        fig.update_layout(title=title, barmode="group")
    else:
        fig = px.bar(df, x=x, y=y, title=title)
    return fig


def _line_chart(df: pd.DataFrame, config: dict) -> go.Figure:
    x = config.get("x")
    y = config.get("y")
    title = config.get("title", "Gráfico de Linhas")
    if isinstance(y, list):
        fig = go.Figure()
        for col in y:
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df[x], y=pd.to_numeric(df[col], errors="coerce"), mode="lines+markers", name=col))
        fig.update_layout(title=title)
    else:
        fig = px.line(df, x=x, y=y, title=title)
    return fig


def _pie_chart(df: pd.DataFrame, config: dict) -> go.Figure:
    x = config.get("x")  # labels
    y = config.get("y")  # values
    title = config.get("title", "Gráfico de Pizza")
    if isinstance(y, list):
        y = y[0]
    return px.pie(df, names=x, values=y, title=title)


def _scatter_chart(df: pd.DataFrame, config: dict) -> go.Figure:
    x = config.get("x")
    y = config.get("y")
    title = config.get("title", "Gráfico de Dispersão")
    if isinstance(y, list):
        y = y[0]
    return px.scatter(df, x=x, y=y, title=title)


def _histogram_chart(df: pd.DataFrame, config: dict) -> go.Figure:
    x = config.get("x") or config.get("y")
    title = config.get("title", "Histograma")
    if isinstance(x, list):
        x = x[0]
    return px.histogram(df, x=x, title=title)


def _heatmap_chart(df: pd.DataFrame, config: dict) -> go.Figure:
    title = config.get("title", "Mapa de Calor")
    numeric = df.select_dtypes(include="number")
    corr = numeric.corr()
    fig = px.imshow(corr, text_auto=True, title=title, color_continuous_scale="RdBu_r")
    return fig


# Mapeamento tipo → gerador
_CHART_GENERATORS = {
    "bar": _bar_chart,
    "line": _line_chart,
    "pie": _pie_chart,
    "scatter": _scatter_chart,
    "histogram": _histogram_chart,
    "heatmap": _heatmap_chart,
}


# -------------------------------------------------------
# Estilo padrão aplicado a todos os gráficos
# -------------------------------------------------------

def _apply_style(fig: go.Figure) -> go.Figure:
    """Aplica tema visual neutro (preto/cinza/branco) consistente com o frontend."""
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=13, color="#333"),
        title_font_size=16,
        paper_bgcolor="white",
        plot_bgcolor="#FAFAFA",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E5E7EB",
            borderwidth=1,
        ),
    )
    return fig


# -------------------------------------------------------
# API pública
# -------------------------------------------------------

def generate_chart(
    df: pd.DataFrame,
    config: dict,
    save_to_disk: bool = True,
) -> dict:
    """Gera um gráfico a partir de um DataFrame e configuração.

    Args:
        df: Dados para plotar.
        config: Dicionário com chart_type, title, x, y, group_by, aggregation.
        save_to_disk: Se True, salva PNG no diretório de mídia.

    Returns:
        dict com:
            "image_bytes": bytes da imagem PNG
            "file_path": caminho relativo salvo (ou None)
            "title": título do gráfico
            "chart_type": tipo do gráfico
    """
    chart_type = config.get("chart_type", "bar")
    generator = _CHART_GENERATORS.get(chart_type)
    if generator is None:
        raise ValueError(f"Tipo de gráfico não suportado: {chart_type}")

    # Aplica agregação se configurada
    plot_df = _apply_aggregation(df.copy(), config)

    # Gera o gráfico
    fig = generator(plot_df, config)
    fig = _apply_style(fig)

    # Exporta como PNG
    image_bytes = fig.to_image(format="png", width=1000, height=600, scale=2)

    file_path = None
    if save_to_disk:
        _ensure_charts_dir()
        filename = f"{uuid.uuid4().hex}.png"
        full_path = CHARTS_DIR / filename
        full_path.write_bytes(image_bytes)
        file_path = f"charts/{filename}"
        logger.info("Gráfico salvo: %s", file_path)

    return {
        "image_bytes": image_bytes,
        "file_path": file_path,
        "title": config.get("title", ""),
        "chart_type": chart_type,
    }


def generate_charts_from_configs(
    dataframes: list[pd.DataFrame],
    chart_configs: list[dict],
) -> list[dict]:
    """Gera múltiplos gráficos a partir das configurações retornadas pela IA.

    Cada config deve ter "source_index" indicando qual DataFrame usar.
    """
    results = []
    for config in chart_configs:
        source_idx = config.get("source_index", 0)
        if source_idx >= len(dataframes):
            logger.warning("source_index %d fora do range (%d fontes)", source_idx, len(dataframes))
            source_idx = 0

        df = dataframes[source_idx]
        try:
            result = generate_chart(df, config)
            results.append(result)
        except Exception as e:
            logger.error("Erro ao gerar gráfico '%s': %s", config.get("title", "?"), e)
            results.append({"error": str(e), "title": config.get("title", ""), "chart_type": config.get("chart_type", "")})

    return results
