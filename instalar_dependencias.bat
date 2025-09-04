@echo off
cd /d "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"

echo ==========================================
echo    INSTALANDO DEPENDENCIAS DO PROJETO
echo ==========================================

echo.
echo [1/2] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo [2/2] Instalando dependencias (pode demorar alguns minutos)...
pip install fastapi uvicorn[standard] sqlmodel SQLAlchemy python-dotenv pandas openpyxl streamlit plotly python-multipart httpx celery redis python-jose pydantic pyjwt requests python-dateutil loguru structlog alembic psycopg2-binary supabase starlette_exporter gunicorn

echo.
echo ==========================================
echo    INSTALACAO CONCLUIDA!
echo ==========================================
echo.
echo Agora você pode rodar o projeto usando:
echo - rodar_projeto.bat
echo.
echo Ou manualmente com os comandos do arquivo COMO_RODAR.md
echo.
pause
