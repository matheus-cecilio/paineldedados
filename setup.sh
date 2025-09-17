#!/usr/bin/env bash

set -e
set -o pipefail

echo "===== Preparando ambiente - terminal bash ====="

# Criar venv se não existir ou se estiver corrompido
if [ ! -d ".venv" ] || ( [ ! -f ".venv/bin/activate" ] && [ ! -f ".venv/Scripts/activate" ] ); then
    echo "Criando ambiente virtual..."
    rm -rf .venv  # remove restos quebrados
    python3 -m venv .venv || { echo "Erro ao criar ambiente virtual."; exit 1; }
else
    echo "Ambiente virtual válido já existe. Pulando criação..."
fi

# Ativar o ambiente virtual (Linux/Mac vs Windows)
if [ -f ".venv/bin/activate" ]; then
    # Linux / Mac
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    # Windows (Git Bash, MSYS, etc.)
    # Verificar e corrigir terminações de linha se necessário
    if grep -q $'\r' .venv/Scripts/activate 2>/dev/null; then
        echo "Corrigindo terminações de linha no arquivo activate..."
        sed -i 's/\r$//' .venv/Scripts/activate
    fi
    source .venv/Scripts/activate
else
    echo "Erro: não foi possível encontrar o script de ativação da venv"
    exit 1
fi

echo "===== Instalando dependências ====="
python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt || {
        echo "Falha ao instalar dependências do requirements.txt"
        exit 1
    }
else
    echo "Nenhum requirements.txt encontrado. Pulando instalação de dependências."
fi

# Criar diretórios se não existirem
mkdir -p uploads sample_data

# Copiar .env.example se .env não existir
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Arquivo .env criado a partir do .env.example"
    else
        echo "Aviso: .env e .env.example não encontrados"
    fi
else
    echo ".env já existe. Pulando criação..."
fi

echo "===== Rodando testes (opcional) ====="
if command -v pytest >/dev/null 2>&1; then
    pytest -q || echo "Testes falharam, mas continuando..."
else
    echo "pytest não encontrado, pulando testes..."
fi


echo "===== Ambiente pronto! ====="
echo "Para rodar o app:"
if [ -f ".venv/bin/activate" ]; then
    echo "  source .venv/bin/activate"
else
    echo "  source .venv/Scripts/activate"
fi
echo "depois: streamlit run app.py"