#!/usr/bin/env bash
# update.sh — Atualiza o projeto na VPS após push no GitHub
#
# USO: ssh deploy@IP_DA_VPS "cd ~/relatoriocep && ./deploy/update.sh"

set -euo pipefail

APP_DIR="/home/deploy/relatoriocep"
cd "$APP_DIR"

echo ">>> Puxando atualizações do GitHub..."
git pull origin main

echo ">>> Atualizando backend..."
cd backend
venv/bin/pip install -r requirements.txt --quiet
venv/bin/python manage.py migrate --no-input
venv/bin/python manage.py collectstatic --no-input

echo ">>> Reconstruindo frontend..."
cd ../frontend
npm install --silent
npm run build

echo ">>> Reiniciando Gunicorn..."
if [ "$(id -u)" -eq 0 ]; then
	systemctl restart relatoriocep
else
	sudo systemctl restart relatoriocep
fi

echo ">>> Atualização concluída!"
