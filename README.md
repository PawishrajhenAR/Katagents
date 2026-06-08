# KatalyzU Agent Platform

Multi-tenant AI business automation platform. Phase 1 delivers the **Email Outreach Agent** MVP.

## Stack

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS v4
- **Backend:** FastAPI, SQLAlchemy 2, Alembic, ARQ
- **Database:** PostgreSQL (Supabase-compatible)
- **Queue:** Redis
- **Auth:** JWT
- **Email:** Resend
- **AI:** Gemini + OpenAI-compatible providers

## Quick start

### Prerequisites

- Node.js 20+ and pnpm
- Python 3.11+
- **PostgreSQL 16** and **Redis 7** (pick one setup path below)

### Option A: Docker (recommended if available)

```bash
docker compose up -d postgres redis
```

### Option B: Native install on Arch Linux (no Docker)

```bash
sudo pacman -S postgresql redis
sudo -u postgres initdb -D /var/lib/postgres/data   # first time only
chmod +x scripts/setup-local-db.sh
./scripts/setup-local-db.sh
```

### Option C: Supabase (cloud Postgres) — **configured**

This repo is linked to Supabase project **`ybvxucxndarcycjzmywt`**.

See **[docs/SUPABASE.md](docs/SUPABASE.md)** for full setup.

**GitHub integration working directory:** `.` (repo root)

1. Copy database password from [Supabase Dashboard → Database](https://supabase.com/dashboard/project/ybvxucxndarcycjzmywt/settings/database)
2. Set in `apps/api/.env`:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_DB_PASSWORD@db.ybvxucxndarcycjzmywt.supabase.co:5432/postgres
```

3. Schema is already applied (`supabase/migrations/20250608000000_initial_schema.sql`). Stamp Alembic so local CLI stays in sync:

```bash
cd apps/api && source .venv/bin/activate && alembic stamp head
```

4. Start API and verify:

```bash
uvicorn main:app --reload --port 8000
curl http://localhost:8000/ready
```

### 1. Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start infrastructure

Use **one** of the options above (Docker, native Postgres, or Supabase).

Verify Postgres is reachable before migrating:

```bash
# Should not show "connection refused"
pg_isready -h localhost -p 5432
```

### 3. Backend

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn main:app --reload --port 8000
```

In another terminal:

```bash
cd apps/api && source .venv/bin/activate
python -m entrypoints.worker
```

### 4. Frontend

```bash
cd apps/web
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

### Full Docker stack

```bash
docker compose up --build
```

## Project structure

```
katagents/
├── apps/
│   ├── api/          # FastAPI + agents + worker
│   └── web/          # Next.js dashboard
├── docker-compose.yml
└── .env.example
```

## API docs

When the API is running: [http://localhost:8000/docs](http://localhost:8000/docs)
