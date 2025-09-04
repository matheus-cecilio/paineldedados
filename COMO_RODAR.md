# 🚀 COMO RODAR O PROJETO - GUIA DEFINITIVO

## 📋 Pré-requisitos
- Python 3.11+ instalado
- Git (opcional)

## 🔧 SETUP INICIAL (Fazer UMA VEZ só)

### 1. Abrir terminal no diretório do projeto
```cmd
cd "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"
```

### 2. Ativar ambiente virtual
```cmd
.venv\Scripts\activate.bat
```

### 3. Instalar dependências (pode demorar alguns minutos)
```cmd
pip install fastapi uvicorn[standard] sqlmodel SQLAlchemy python-dotenv pandas openpyxl streamlit plotly python-multipart httpx celery redis python-jose pydantic pyjwt requests python-dateutil loguru structlog alembic psycopg2-binary supabase starlette_exporter gunicorn
```

## 🎯 RODAR O PROJETO (Todo dia que for usar)

### Terminal 1 - Backend (FastAPI)
```cmd
cd "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"
.venv\Scripts\activate.bat
python -m uvicorn backend.app.main:app --reload --port 8000
```

### Terminal 2 - Dashboard (Streamlit)
```cmd
cd "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"
.venv\Scripts\activate.bat
python -m streamlit run dashboard\streamlit_app.py --server.port 8501
```

## 🌐 URLs para acessar

- **API Backend**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

## 🔄 SCRIPT AUTOMATIZADO

### Windows Batch (rodar_projeto.bat)
Crie um arquivo `rodar_projeto.bat` e cole o conteúdo abaixo:

```batch
@echo off
cd /d "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"

echo ==========================================
echo    INICIANDO PAINEL DE VENDAS
echo ==========================================

echo.
echo [1/3] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo [2/3] Iniciando Backend (FastAPI)...
start "Backend API" cmd /k "cd /d "%CD%" && .venv\Scripts\activate.bat && python -m uvicorn backend.app.main:app --reload --port 8000"

echo.
echo [3/3] Aguardando 5 segundos e iniciando Dashboard...
timeout /t 5 /nobreak >nul

start "Dashboard Streamlit" cmd /k "cd /d "%CD%" && .venv\Scripts\activate.bat && python -m streamlit run dashboard\streamlit_app.py --server.port 8501"

echo.
echo ==========================================
echo    PROJETO INICIADO COM SUCESSO!
echo ==========================================
echo.
echo URLs:
echo - API Backend: http://localhost:8000/docs
echo - Dashboard:   http://localhost:8501
echo.
echo Pressione qualquer tecla para abrir os URLs...
pause >nul

start http://localhost:8000/docs
start http://localhost:8501

echo.
echo Para parar os serviços, feche as janelas do terminal
echo ou pressione Ctrl+C em cada uma.
pause
```

## ⚡ USO RÁPIDO

1. **Primeira vez**: Execute os comandos da seção "SETUP INICIAL"
2. **Toda vez que for usar**: Execute o arquivo `rodar_projeto.bat` OU os comandos da seção "RODAR O PROJETO"
3. **Acesse**: http://localhost:8501 para o dashboard

## 🛠️ Solução de Problemas

### Erro: 'uvicorn' não é reconhecido
```cmd
python -m uvicorn backend.app.main:app --reload --port 8000
```

### Erro: 'streamlit' não é reconhecido
```cmd
python -m streamlit run dashboard\streamlit_app.py --server.port 8501
```

### Erro de conexão no dashboard
- Verifique se o backend está rodando na porta 8000
- Aguarde alguns segundos após iniciar o backend

### Erro de dependências faltando
```cmd
.venv\Scripts\activate.bat
pip install -r backend\requirements.txt
pip install streamlit plotly
```

## 📁 Estrutura de Arquivos Importante

```
paineldevendas/
├── .venv/                  # Ambiente virtual Python
├── backend/                # API FastAPI
├── dashboard/              # Interface Streamlit
├── .env                    # Configurações
└── rodar_projeto.bat       # Script para rodar tudo
```

## 🎯 Funcionalidades Principais

1. **Upload de Excel**: Faça upload de planilhas no dashboard
2. **API REST**: Endpoints para integração
3. **Visualizações**: Gráficos e KPIs em tempo real
4. **Banco Local**: SQLite para desenvolvimento

---

**💡 Dica**: Salve este arquivo e use sempre que precisar rodar o projeto!
