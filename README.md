# Painel Automatizado de Dados (Python + PostgreSQL + Supabase)

Este repositório contém um MVP completo para importar planilhas Excel, armazenar em PostgreSQL (ou SQLite em dev), expor API FastAPI, e visualizar KPIs em um painel Streamlit. Inclui Celery/Redis (com modo eager para rodar localmente sem Redis), migrações Alembic, testes, e CI.

## Rodar localmente
Pré-requisitos: Python 3.11+

1. Crie e ative um ambiente virtual e instale dependências:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
pip install -r backend\app\tests\requirements-test.txt
```
2. Configure variáveis (modo local usa SQLite e Celery eager):
```
copy .env.example .env
```
3. Inicie o backend (FastAPI):
```
uvicorn backend.app.main:app --reload --port 8000
```
4. Em outro terminal, inicie o dashboard Streamlit:
```
streamlit run dashboard\streamlit_app.py --server.port 8501
```
5. Acesse: API http://localhost:8000/docs, Dashboard http://localhost:8501.

Observação: Em dev local, `API_AUTH_BYPASS=true` e `CELERY_TASK_ALWAYS_EAGER=true`, então endpoints protegidos passam sem JWT e tarefas Celery executam no processo, sem Redis.

## Migrações (opcional em SQLite)
Para SQLite, o app cria a estrutura automaticamente no startup. Para Postgres/Supabase, rode:
```
alembic -c backend\alembic.ini upgrade head
```

## Rodar testes
```
pytest -q
```

## Docker (opcional)
Arquivos Docker e docker-compose estão presentes mas não são necessários para dev local.

## Supabase (produção)
1. Crie um projeto no Supabase.
2. Obtenha: URL do projeto, anon key e service_role key.
3. Defina `DATABASE_URL` para o banco do Supabase (formato em `.env.example`).
4. Rode as migrações apontando para o Supabase:
```
DATABASE_URL=postgresql+psycopg2://postgres:<password>@db.<ref>.supabase.co:5432/postgres \
  alembic -c backend/alembic.ini upgrade head
```
5. Configure variáveis no deploy (backend): `DATABASE_URL`, `REDIS_URL`, `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_JWT_AUDIENCE`.

## Testes
Instale dependências e rode:
```
pip install -r backend/requirements.txt
pytest -q
```

## Lint
```
pip install black isort flake8
black backend/app
isort backend/app
flake8 backend/app
```

## API (principais rotas)
- POST `/auth/verify` — valida JWT (ou bypass em dev)
- POST `/import` — upload .xlsx → job_id
- GET `/import/{job_id}/status`
- CRUD: `/products`, `/customers`, `/categories`, `/sales`
- GET `/dashboard/summary?start=YYYY-MM-DD&end=YYYY-MM-DD`

## Observações / TODOs
- Implementar validação completa de JWT com JWKS do Supabase quando em produção.
- Adicionar paginação/contagem total nas listas (headers ou envelope).
- Rate limiting e Sentry (opcional) para produção.
- Melhorias de performance no import (bulk insert) e índices no DB.
- Webhook FRONTEND_WEBHOOK_URL pode ser usado para notificar conclusão do import.

## Licença
MIT
