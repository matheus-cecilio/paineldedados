#!/usr/bin/env bash
set -euo pipefail

# Helper script to outline Supabase deploy steps.

if [ -z "${SUPABASE_PROJECT_REF:-}" ]; then
  echo "Set SUPABASE_PROJECT_REF (project ref id) and SUPABASE_DB_PASSWORD in your environment."
fi

cat <<'DOC'
Steps to deploy to Supabase:
1) Create a Supabase project and get:
   - Project URL
   - anon key
   - service_role key
   - Project ref id (in Project Settings -> General)
2) Create a database password for the 'postgres' user.
3) In GitHub repo settings -> Secrets and variables -> Actions, set secrets:
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - SUPABASE_SERVICE_ROLE_KEY
   - DATABASE_URL (e.g., postgresql+psycopg2://postgres:<password>@db.<ref>.supabase.co:5432/postgres)
4) Run Alembic migrations against Supabase DB:
   DATABASE_URL=postgresql+psycopg2://postgres:<password>@db.<ref>.supabase.co:5432/postgres \
   alembic -c backend/alembic.ini upgrade head
5) Configure your hosting to run the backend container with env vars above.
DOC
