@echo off
cd /d "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"

echo ==========================================
echo    CONFIGURACAO INICIAL DO GIT
echo ==========================================

echo.
echo [1/5] Inicializando repositório git...
git init

echo.
echo [2/5] Configurando usuário git...
echo Digite seu nome completo:
set /p git_name="Nome: "
git config user.name "%git_name%"

echo.
echo Digite seu email do GitHub:
set /p git_email="Email: "
git config user.email "%git_email%"

echo.
echo [3/5] Configurando branch principal...
git branch -M main

echo.
echo [4/5] Adicionando arquivos...
git add .

echo.
echo [5/5] Primeiro commit...
git commit -m "Initial commit - Painel de Vendas"

echo.
echo ==========================================
echo    CONFIGURACAO CONCLUIDA!
echo ==========================================
echo.
echo Próximos passos:
echo 1. Crie um repositório no GitHub
echo 2. Copie a URL do repositório
echo 3. Execute: git remote add origin URL_DO_REPOSITORIO
echo 4. Execute: git push -u origin main
echo.
echo Ou use o script git_commit_push.bat para commits futuros
echo.
pause
