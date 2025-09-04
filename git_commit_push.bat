@echo off
cd /d "c:\Users\operacional1\OneDrive - OrionLift\Documentos\Modelos Personalizados do Office\paineldevendas"

echo ==========================================
echo    GIT COMMIT E PUSH AUTOMATICO
echo ==========================================

echo.
echo [1/4] Verificando status do git...
git status

echo.
echo [2/4] Adicionando todos os arquivos...
git add .

echo.
echo Digite a mensagem do commit (ou Enter para usar mensagem padrão):
set /p commit_msg="Mensagem: "

if "%commit_msg%"=="" (
    set commit_msg=Atualizacao automatica - %date% %time%
)

echo.
echo [3/4] Fazendo commit com mensagem: "%commit_msg%"
git commit -m "%commit_msg%"

echo.
echo [4/4] Fazendo push para o repositório...
git push

echo.
echo ==========================================
echo    COMMIT E PUSH CONCLUIDOS!
echo ==========================================
echo.
echo O CI/CD vai rodar automaticamente no GitHub
echo Verifique em: https://github.com/seu-usuario/seu-repo/actions
echo.
pause
