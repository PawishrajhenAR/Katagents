#!/usr/bin/env bash
# Local Postgres + Redis setup for Arch Linux (no Docker).
set -euo pipefail

echo "==> Checking PostgreSQL..."
if ! command -v psql >/dev/null 2>&1; then
  echo "PostgreSQL not found. Install with:"
  echo "  sudo pacman -S postgresql redis"
  exit 1
fi

echo "==> Enabling PostgreSQL service..."
sudo systemctl enable --now postgresql

echo "==> Creating database user and database (if missing)..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = 'katalyzu'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER katalyzu WITH PASSWORD 'katalyzu';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'katalyzu'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE katalyzu OWNER katalyzu;"

echo "==> Enabling Redis (optional, for background worker)..."
if command -v redis-cli >/dev/null 2>&1; then
  sudo systemctl enable --now redis 2>/dev/null || sudo systemctl enable --now redis-server 2>/dev/null || true
fi

echo "==> Running migrations..."
cd "$(dirname "$0")/../apps/api"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -e ".[dev]"
fi
.venv/bin/alembic upgrade head

echo ""
echo "Done. Start the API with:"
echo "  cd apps/api && source .venv/bin/activate && uvicorn main:app --reload --port 8000"
