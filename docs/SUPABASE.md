# Supabase ↔ KatalyzU

Project: **ybvxucxndarcycjzmywt**  
API URL: **https://ybvxucxndarcycjzmywt.supabase.co**

## GitHub integration (Supabase Dashboard)

When linking this repo in Supabase:

| Field | Value |
|-------|-------|
| **Working directory** | `.` |
| **Migrations path** | `supabase/migrations/` |

## Local API connection

1. Open [Supabase Dashboard](https://supabase.com/dashboard/project/ybvxucxndarcycjzmywt/settings/database)
2. Copy your **database password** (or reset it)
3. Set in `apps/api/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_DB_PASSWORD@db.ybvxucxndarcycjzmywt.supabase.co:5432/postgres
SUPABASE_URL=https://ybvxucxndarcycjzmywt.supabase.co
SUPABASE_PROJECT_REF=ybvxucxndarcycjzmywt
```

For serverless/pooled connections (production), use the **Session pooler** URI from the dashboard (port 6543) instead.

4. Start the API:

```bash
cd apps/api && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```

## Schema management

- **Remote (Supabase):** migrations in `supabase/migrations/` — applied via Supabase MCP or `supabase db push`
- **Local Alembic:** `apps/api/migrations/` — keep in sync when changing schema; update both or prefer Supabase migrations for production

Initial schema `initial_schema` is already applied to your Supabase project (21 tables).

## Verify connection

```bash
curl http://localhost:8000/ready
```

Should return `{"status":"ready"}` once `DATABASE_URL` is set correctly.
