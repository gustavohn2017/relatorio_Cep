"""
reports/services/ai_analysis.py — Análise de dados com IA via Groq.

A Groq oferece modelos LLM rápidos (LLaMA 3, Mixtral) com latência
muito baixa, ideal para análises interativas.

Funcionalidades:
  • Recebe um ou mais DataFrames e o prompt do usuário
  • Monta contexto com amostra dos dados + estatísticas descritivas
  • Envia para a Groq API e retorna a análise em Markdown
  • Suporta comparação entre múltiplas fontes
  • Detecta se o usuário quer gráficos e retorna instruções de plotagem
"""

import json
import logging

import pandas as pd
from django.conf import settings
from groq import Groq

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Inicialização do client Groq
# -------------------------------------------------------
_groq_client: Groq | None = None


def _get_groq_client() -> Groq:
    """Singleton do client Groq."""
    global _groq_client
    if _groq_client is None:
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise RuntimeError("GROQ_API_KEY não configurada. Verifique o .env")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# -------------------------------------------------------
# Preparação do contexto de dados
# -------------------------------------------------------

# Limite de linhas amostradas para enviar ao LLM (evita estourar tokens)
MAX_SAMPLE_ROWS = 80


def _dataframe_summary(df: pd.DataFrame, name: str = "Dados") -> str:
    """Gera um resumo textual de um DataFrame para uso como contexto do LLM."""
    lines = [f"### {name}"]
    lines.append(f"- **Dimensões**: {df.shape[0]} linhas × {df.shape[1]} colunas")
    lines.append(f"- **Colunas**: {', '.join(df.columns.tolist())}")

    # Tipos de dados
    lines.append(f"- **Tipos**: {df.dtypes.to_dict()}")

    # Estatísticas descritivas (apenas numéricos)
    numeric_cols = df.select_dtypes(include="number")
    if not numeric_cols.empty:
        desc = numeric_cols.describe().to_string()
        lines.append(f"\n**Estatísticas descritivas:**\n```\n{desc}\n```")

    # Valores nulos
    null_counts = df.isnull().sum()
    if null_counts.any():
        lines.append(f"\n**Valores nulos por coluna:**\n{null_counts[null_counts > 0].to_dict()}")

    # Amostra das primeiras linhas
    sample_size = min(MAX_SAMPLE_ROWS, len(df))
    sample = df.head(sample_size).to_csv(index=False)
    lines.append(f"\n**Amostra ({sample_size} linhas):**\n```csv\n{sample}\n```")

    return "\n".join(lines)


# -------------------------------------------------------
# Prompt do sistema
# -------------------------------------------------------

SYSTEM_PROMPT = """Você é um analista de dados sênior. O usuário vai fornecer dados tabulares e fazer perguntas sobre eles.

Regras:
1. Responda sempre em **português brasileiro**.
2. Use Markdown para formatar sua resposta (títulos, listas, tabelas, etc.).
3. Seja detalhado e preciso nas análises.
4. Se receber múltiplas fontes de dados, compare-as quando relevante.
5. Se o usuário pedir gráficos, inclua no final da resposta um bloco JSON especial delimitado por ```chart_config ... ``` contendo uma lista de objetos com:
   - "chart_type": "bar" | "line" | "pie" | "scatter" | "histogram" | "heatmap"
   - "title": título do gráfico
   - "x": nome da coluna para eixo X (ou null)
   - "y": nome da coluna para eixo Y (ou lista de colunas)
   - "source_index": índice da fonte de dados (0, 1, 2...)
   - "aggregation": null | "sum" | "mean" | "count" | "max" | "min"
   - "group_by": null | nome da coluna para agrupar
6. Não invente dados. Baseie-se apenas nas informações fornecidas.
7. Se os dados forem insuficientes para responder, diga explicitamente.
"""


# -------------------------------------------------------
# Função principal de análise
# -------------------------------------------------------


def analyze(
    dataframes: list[pd.DataFrame],
    source_names: list[str],
    user_prompt: str,
    model: str = "llama-3.3-70b-versatile",
) -> dict:
    """Envia dados + prompt para a Groq e retorna análise.

    Args:
        dataframes: Lista de DataFrames a analisar.
        source_names: Nomes correspondentes a cada DF.
        user_prompt: Pergunta/instrução do usuário.
        model: Modelo Groq a utilizar.

    Returns:
        dict com:
            "analysis": texto Markdown da resposta
            "chart_configs": lista de dicts de configuração de gráficos (pode ser vazia)
            "model_used": modelo utilizado
            "usage": informações de uso de tokens
    """
    client = _get_groq_client()

    # Monta o contexto com resumo de cada fonte de dados
    context_parts = []
    for i, (df, name) in enumerate(zip(dataframes, source_names)):
        context_parts.append(_dataframe_summary(df, name=f"Fonte {i + 1}: {name}"))

    data_context = "\n\n---\n\n".join(context_parts)

    user_message = f"""## Dados disponíveis

{data_context}

---

## Pergunta do usuário

{user_prompt}"""

    logger.info(
        "Enviando análise para Groq (modelo=%s, fontes=%d, prompt=%d chars)",
        model,
        len(dataframes),
        len(user_prompt),
    )

    # Chamada à API Groq
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=8192,
    )

    response_text = chat_completion.choices[0].message.content

    # Extrai configurações de gráficos se a IA incluiu
    chart_configs = _extract_chart_configs(response_text)

    # Remove o bloco chart_config do texto principal para exibição limpa
    clean_text = _remove_chart_config_block(response_text)

    return {
        "analysis": clean_text,
        "chart_configs": chart_configs,
        "model_used": model,
        "usage": {
            "prompt_tokens": chat_completion.usage.prompt_tokens,
            "completion_tokens": chat_completion.usage.completion_tokens,
            "total_tokens": chat_completion.usage.total_tokens,
        },
    }


# -------------------------------------------------------
# Helpers para extração de chart_config
# -------------------------------------------------------

def _extract_chart_configs(text: str) -> list[dict]:
    """Extrai blocos ```chart_config ... ``` da resposta da IA."""
    import re

    pattern = r"```chart_config\s*([\s\S]*?)```"
    matches = re.findall(pattern, text)

    configs = []
    for match in matches:
        try:
            parsed = json.loads(match.strip())
            if isinstance(parsed, list):
                configs.extend(parsed)
            elif isinstance(parsed, dict):
                configs.append(parsed)
        except json.JSONDecodeError:
            logger.warning("Não foi possível parsear chart_config: %s", match[:200])
    return configs


def _remove_chart_config_block(text: str) -> str:
    """Remove blocos chart_config do texto para exibição limpa."""
    import re

    return re.sub(r"```chart_config\s*[\s\S]*?```", "", text).strip()
