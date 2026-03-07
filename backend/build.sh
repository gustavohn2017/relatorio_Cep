#!/usr/bin/env bash
# build.sh — Script de build para deploy no Render.
# Executado automaticamente antes de iniciar o servidor.

set -o errexit  # Aborta em caso de erro

# Instala dependências Python
pip install -r requirements.txt

# Coleta arquivos estáticos (CSS/JS do admin, etc.)
python manage.py collectstatic --no-input

# Aplica migrations no banco de dados
python manage.py migrate --no-input
