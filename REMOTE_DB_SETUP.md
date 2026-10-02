# Remote SQL setup (data survives VPS / RDP change)

Bot supports two modes:

1. **Local SQLite** (default) — file `bot_data.db` on the server (lost if disk wiped)
2. **Remote PostgreSQL** — set `DATABASE_URL` (Neon / Supabase / Railway)

## Free option: Neon (recommended)

1. Open https://neon.tech → Sign up
2. Create project (region: Singapore / closest)
3. Dashboard → Connection string → copy **URI**
   Example:
   ```
   postgresql://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. On VPS / Render / Railway set env:
   ```
   DATABASE_URL=postgresql://user:pass@HOST/neondb?sslmode=require
   ```
5. Install driver:
   ```
   pip install psycopg2-binary
   ```
6. Start bot:
   ```
   python bot.py
   ```
   Logs should show: `DB backend: PostgreSQL (remote)`

## Supabase

1. https://supabase.com → New project
2. Settings → Database → Connection string (URI)
3. Same `DATABASE_URL=...` env

## Notes

- Users, credits, VIP, contacts, settings, logs → remote SQL
- External OSINT `.db` files (leak DBs) stay as separate files (max 20 × 3GB)
- Changing VPS: only copy bot code + set same `DATABASE_URL` — data already in cloud
- Leave `DATABASE_URL` empty to use local SQLite

## Migrate existing local SQLite → Postgres (optional)

Use any SQLite→Postgres tool, or re-add VIP users after switch (fresh cloud DB).
