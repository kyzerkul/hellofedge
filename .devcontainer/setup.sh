#!/usr/bin/env bash
# Préparation du Codespace, lancée une fois à sa création : uv, dépendances, base.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> uv"
pip install --quiet --user uv
export PATH="$HOME/.local/bin:$PATH"

echo "==> Dépendances Python"
(cd backend && uv sync --locked)

echo "==> Base des tests"
(cd backend && uv run python - <<'EOF'
import psycopg
with psycopg.connect("postgresql://hellofedge:hellofedge@db:5432/hellofedge", autocommit=True) as c:
    if not c.execute("SELECT 1 FROM pg_database WHERE datname = 'hellofedge_test'").fetchone():
        c.execute("CREATE DATABASE hellofedge_test")
EOF
)

echo "==> Migrations"
(cd backend && uv run alembic upgrade head)

echo
echo "Codespace prêt. Lance : bash .devcontainer/mesure.sh"
