# RelatórioCEP — Análise de Dados com IA

Aplicação web full-stack para análise inteligente de planilhas e dados tabulares, utilizando **Django** (backend), **React + Tailwind** (frontend) e **Groq AI** (análise por LLM).

---

## Funcionalidades

- **Múltiplas fontes de dados**: Google Sheets (com navegação entre abas), CSV, Excel (.xlsx), XML, PDF e arquivos de texto
- **Análise por IA (Groq)**: modelo LLaMA 3.3 70B para análises detalhadas, comparações entre fontes e respostas em português
- **Geração de gráficos**: barras, linhas, pizza, dispersão, histograma e mapa de calor (Plotly)
- **Comparação simultânea**: analise múltiplos links/arquivos de uma só vez
- **Google Sheets restrito**: compartilhe a planilha com o e-mail do Service Account — sem OAuth complexo
- **Sistema de login completo**: registro, JWT, recuperação de senha por e-mail
- **Histórico**: consulte análises anteriores (requer login)
- **Uso sem login**: a análise funciona sem cadastro; o login é necessário apenas para o histórico
- **Suporte a larga escala**: otimizado com Pandas para planilhas com muitas linhas e colunas

---

## Arquitetura

```
RelatorioCEP/
├── backend/                  # Django + DRF
│   ├── core/                 # Settings, URLs, WSGI
│   ├── accounts/             # Auth, registro, recuperação de senha
│   ├── reports/              # Modelos, views e serviços
│   │   ├── services/
│   │   │   ├── google_sheets.py    # Integração Google Sheets (gspread)
│   │   │   ├── file_parsers.py     # Parsers CSV/Excel/XML/PDF/TXT
│   │   │   ├── ai_analysis.py      # Análise com Groq (LLaMA 3)
│   │   │   └── chart_generator.py  # Geração de gráficos (Plotly)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React + Vite + Tailwind
│   ├── src/
│   │   ├── components/       # Layout, Navbar
│   │   ├── context/          # AuthContext (JWT)
│   │   ├── pages/            # Home, Login, Register, History...
│   │   ├── api.js            # Axios com interceptors JWT
│   │   └── App.jsx           # Roteamento
│   └── package.json
└── README.md
```

---

## Pré-requisitos

- **Python** 3.11+
- **Node.js** 18+
- **Conta Groq** com API key (gratuita): https://console.groq.com
- **Google Cloud Console** (opcional, para Google Sheets):
  - Service Account com Google Sheets API habilitada

---

## Setup Rápido

### 1. Backend (Django)

```bash
cd backend

# Criar e ativar virtualenv
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
copy .env.example .env
# Edite o .env com suas chaves (GROQ_API_KEY, e-mail, etc.)

# Rodar migrations
python manage.py migrate

# Criar superusuário (opcional)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### 2. Frontend (React)

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar dev server
npm run dev
```

Acesse: **http://localhost:5173**

---

## Configuração do Google Sheets

### Passo a passo:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Crie um projeto (ou use um existente)
3. Ative a **Google Sheets API**
4. Vá em **IAM & Admin → Service Accounts** e crie uma conta de serviço
5. Gere uma chave JSON e salve em `backend/credentials/google_service_account.json`
6. No `.env`, configure:
   ```
   GOOGLE_CREDENTIALS_FILE=credentials/google_service_account.json
   ```
7. **Compartilhe a planilha** com o e-mail do Service Account (ex: `meu-bot@meu-projeto.iam.gserviceaccount.com`) como **Leitor**

> Na interface web, clique em "Ver e-mail para compartilhamento" para ver o e-mail exato.

---

## Configuração do Groq AI

1. Crie uma conta em https://console.groq.com
2. Gere uma API Key
3. No `.env`:
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
   ```

O modelo padrão é `llama-3.3-70b-versatile` (rápido e gratuito no tier free).

---

## Configuração de E-mail (Recuperação de Senha)

Para Gmail com "Senhas de app":

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-16-chars
```

> Em desenvolvimento, use `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` para ver os e-mails no terminal.

---

## API Endpoints

### Autenticação (`/api/auth/`)

| Método | Endpoint                     | Descrição                    |
|--------|------------------------------|------------------------------|
| POST   | `/api/auth/register/`        | Criar conta                  |
| POST   | `/api/auth/token/`           | Login (JWT)                  |
| POST   | `/api/auth/token/refresh/`   | Renovar token                |
| GET    | `/api/auth/me/`              | Dados do usuário logado      |
| POST   | `/api/auth/password-reset/`  | Solicitar recuperação        |
| POST   | `/api/auth/password-reset-confirm/` | Redefinir senha       |

### Relatórios (`/api/reports/`)

| Método | Endpoint                     | Descrição                    |
|--------|------------------------------|------------------------------|
| POST   | `/api/reports/analyze/`      | Análise com IA (principal)   |
| POST   | `/api/reports/upload/`       | Upload de arquivo            |
| POST   | `/api/reports/sheets/tabs/`  | Listar abas Google Sheets    |
| GET    | `/api/reports/sheets/email/` | E-mail do Service Account    |
| GET    | `/api/reports/history/`      | Histórico (autenticado)      |
| GET    | `/api/reports/history/:id/`  | Detalhe de relatório         |
| DELETE | `/api/reports/history/:id/`  | Excluir relatório            |

---

## Tecnologias

| Camada     | Tecnologias                                          |
|------------|------------------------------------------------------|
| Backend    | Django 5, Django REST Framework, SimpleJWT            |
| Dados      | Pandas, openpyxl, pdfplumber, lxml, gspread           |
| IA         | Groq API (LLaMA 3.3 70B Versatile)                   |
| Gráficos   | Plotly                                                |
| Frontend   | React 19, React Router 7, Tailwind CSS 3              |
| HTTP       | Axios com interceptors JWT                            |

---

## Licença

Projeto privado — uso interno.
