#!/usr/bin/env bash
set -e
echo "Criando ambiente virtual..."
python3 -m venv .venv
if [[ "$(uname -s)" == "Linux" || "$(uname -s)" == "Darwin" ]]; then
	source .venv/bin/activate
else
	# Para Windows (Git Bash, MSYS, etc.)
	source .venv/Scripts/activate
fi
echo "Instalando dependências..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
mkdir -p uploads sample_data
if [ ! -f .env ]; then cp .env.example .env; fi
pytest -q || true
echo "Para rodar o app: 
Se você está usando o Git Bash, use:
source .venv/Scripts/activate streamlit run app.py

Se estiver usando o cmd.exe, use:
.venv\Scripts\activate.bat streamlit run app.py
"
