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
