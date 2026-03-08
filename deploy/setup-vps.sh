#!/usr/bin/env bash
# ============================================================
# setup-vps.sh — Script de deploy para VPS Hostinger (Ubuntu)
# ============================================================
# USO: Execute como root na VPS:
#   chmod +x setup-vps.sh && sudo ./setup-vps.sh
#
# O que este script faz:
#   1. Atualiza o sistema
#   2. Instala Python 3.12, PostgreSQL, Nginx, Node.js 20
#   3. Cria usuário "deploy"
#   4. Configura o banco de dados
#   5. Clona o repositório
#   6. Configura backend (venv, migrations)
#   7. Build do frontend
#   8. Configura Nginx e Gunicorn (systemd)
#   9. Instala SSL com Certbot (opcional)
# ============================================================

set -euo pipefail

# ===================== VARIÁVEIS =====================
REPO_URL="https://github.com/gustavohn2017/relatorio_Cep.git"
APP_DIR="/home/deploy/relatoriocep"
DB_NAME="relatoriocep_db"
DB_USER="relatoriocep_user"
DOMAIN=""  # Preencha se tiver domínio, senão deixe vazio

echo "================================================"
echo "  RelatorioCEP — Setup VPS Hostinger"
echo "================================================"

# 1. Atualizar sistema
echo "[1/9] Atualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependências do sistema
echo "[2/9] Instalando dependências..."
apt install -y \
    python3 python3-venv python3-pip python3-dev \
    postgresql postgresql-contrib libpq-dev \
    nginx certbot python3-certbot-nginx \
    git curl build-essential

# Instalar Node.js 20 via NodeSource
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi

echo "  Python: $(python3 --version)"
echo "  Node:   $(node --version)"
echo "  npm:    $(npm --version)"

# 3. Criar usuário deploy (se não existir)
echo "[3/9] Configurando usuário deploy..."
if ! id -u deploy &>/dev/null; then
    useradd -m -s /bin/bash deploy
    usermod -aG www-data deploy
fi

# 4. Configurar PostgreSQL
echo "[4/9] Configurando PostgreSQL..."
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 32)
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "  Banco: ${DB_NAME}"
echo "  Usuário: ${DB_USER}"
echo "  Senha: ${DB_PASSWORD}"
echo ""
echo "  >>> ANOTE A SENHA DO BANCO! <<<"
echo ""

# 5. Clonar repositório
echo "[5/9] Clonando repositório..."
if [ -d "$APP_DIR" ]; then
    echo "  Diretório já existe, fazendo pull..."
    sudo -u deploy git -C "$APP_DIR" pull origin main
else
    sudo -u deploy git clone "$REPO_URL" "$APP_DIR"
fi

# 6. Configurar backend
echo "[6/9] Configurando backend Django..."
cd "$APP_DIR/backend"

# Criar venv
sudo -u deploy python3 -m venv venv
sudo -u deploy venv/bin/pip install --upgrade pip
sudo -u deploy venv/bin/pip install -r requirements.txt
sudo -u deploy venv/bin/pip install psycopg2-binary

# Gerar SECRET_KEY
DJANGO_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Criar .env de produção
cat > .env << EOF
SECRET_KEY=${DJANGO_SECRET}
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1${DOMAIN:+,$DOMAIN}

DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

CORS_ALLOWED_ORIGINS=http://localhost${DOMAIN:+,https://$DOMAIN}
CSRF_TRUSTED_ORIGINS=http://localhost${DOMAIN:+,https://$DOMAIN}

GROQ_API_KEY=
GOOGLE_CREDENTIALS_FILE=${APP_DIR}/backend/credentials/google_service_account.json

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EOF

chown deploy:deploy .env
chmod 600 .env

# Criar diretório de credenciais
sudo -u deploy mkdir -p credentials media

# Migrations e static
sudo -u deploy venv/bin/python manage.py migrate --no-input
sudo -u deploy venv/bin/python manage.py collectstatic --no-input

# 7. Build do frontend
echo "[7/9] Fazendo build do frontend..."
cd "$APP_DIR/frontend"

# Criar .env com API URL (mesmo servidor, usa /api)
sudo -u deploy bash -c "echo 'VITE_API_URL=/api' > .env"
sudo -u deploy npm install
sudo -u deploy npm run build

# 8. Configurar Nginx
echo "[8/9] Configurando Nginx..."
SERVER_NAME="${DOMAIN:-$(curl -s ifconfig.me)}"

# Copiar config do Nginx adaptando o domínio/IP
sed "s|SEU_DOMINIO_OU_IP|${SERVER_NAME}|g" \
    "$APP_DIR/deploy/nginx.conf" > /etc/nginx/sites-available/relatoriocep

ln -sf /etc/nginx/sites-available/relatoriocep /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx

# Configurar Gunicorn (systemd)
mkdir -p /var/log/relatoriocep
chown deploy:www-data /var/log/relatoriocep

cp "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/relatoriocep.service
systemctl daemon-reload
systemctl enable --now relatoriocep

# 9. SSL (se tiver domínio)
if [ -n "$DOMAIN" ]; then
    echo "[9/9] Configurando SSL com Certbot..."
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@${DOMAIN}"
else
    echo "[9/9] SSL ignorado (sem domínio configurado)."
    echo "  Quando tiver um domínio, execute:"
    echo "  sudo certbot --nginx -d seudominio.com"
fi

echo ""
echo "================================================"
echo "  DEPLOY CONCLUÍDO!"
echo "================================================"
echo ""
echo "  App:    http://${SERVER_NAME}"
echo "  Admin:  http://${SERVER_NAME}/admin/"
echo "  API:    http://${SERVER_NAME}/api/"
echo ""
echo "  PRÓXIMOS PASSOS:"
echo "  1. Edite /home/deploy/relatoriocep/backend/.env"
echo "     e adicione sua GROQ_API_KEY"
echo "  2. sudo systemctl restart relatoriocep"
echo "  3. Se tiver domínio, configure o DNS e rode:"
echo "     sudo certbot --nginx -d seudominio.com"
echo ""
echo "  Senha do banco PostgreSQL: ${DB_PASSWORD}"
echo "  >>> ANOTE ESTA SENHA! <<<"
echo "================================================"
