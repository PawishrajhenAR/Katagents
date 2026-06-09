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

The API loads env from **`apps/api/.env` first**, then **repo root `.env`** (root wins if both define the same key). You can keep `DATABASE_URL` in either file.

1. Open [Supabase Dashboard → Database settings](https://supabase.com/dashboard/project/ybvxucxndarcycjzmywt/settings/database)
2. Copy your **database password** (or reset it). URL-encode special characters in the connection string (`@` → `%40`, `#` → `%23`).
3. Prefer the **Session pooler** URI (not the direct `db.*.supabase.co` host):

   - Direct host is **IPv6-only**; many local networks refuse it → `Connection refused` on signup.
   - Session pooler has IPv4 and works from most dev machines.

   In the dashboard: **Connect** → **Session pooler** → copy the URI, then switch the scheme for this API:

```env
# Example shape — replace REGION and password from your dashboard
DATABASE_URL=postgresql+asyncpg://postgres.ybvxucxndarcycjzmywt:YOUR_URL_ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
```

Set in **repo root `.env`** and/or **`apps/api/.env`**:

```env
SUPABASE_URL=https://ybvxucxndarcycjzmywt.supabase.co
SUPABASE_PROJECT_REF=ybvxucxndarcycjzmywt
```

4. Restart the API after changing env (uvicorn reload does not always re-read `.env`):

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
