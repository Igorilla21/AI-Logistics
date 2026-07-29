# Local PostgreSQL Setup

Last updated: 2026-06-18

## Goal

Use PostgreSQL for local runtime work before adding authentication or other production-oriented persistence changes.

The repository already supports PostgreSQL through `DYNNO_DATABASE_URL`, SQLAlchemy, and Alembic. This guide only adds a repeatable local setup path.

## Local Container

The repository now includes `docker-compose.postgres.yml` with one local PostgreSQL service.

Runtime characteristics:

- database: `dynno_customs`
- user: `dynno_customs`
- password: `dynno_customs_local`
- port: `5432`
- data directory: `storage/postgres/`

This keeps local database state inside the project directory instead of a system-level temp or unnamed external volume.

## Start PostgreSQL

From the repository root:

```powershell
docker compose -f docker-compose.postgres.yml up -d
```

Check health:

```powershell
docker compose -f docker-compose.postgres.yml ps
```

## Backend Environment

Create `backend/.env` with a PostgreSQL connection string such as:

```env
DYNNO_DATABASE_URL=postgresql+psycopg://dynno_customs:dynno_customs_local@127.0.0.1:5432/dynno_customs
DYNNO_DATABASE_ECHO=false
```

Keep other runtime paths project-local unless there is a deliberate deployment reason to move them.

## Run Migrations

From `backend/`:

```powershell
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```

## Verify Runtime

After migrations:

1. start the backend with the project-local virtual environment;
2. confirm startup completes without database errors;
3. call `/api/health`;
4. create one validation run and confirm new records land in PostgreSQL instead of the default SQLite file.

## What This Changes

After the environment switch:

- metadata and validation history should persist in PostgreSQL;
- future auth tables should also be created in PostgreSQL;
- uploaded source files and OCR text still remain file-based under project-local runtime directories unless storage architecture is changed later.

## Recommended Next Step

After PostgreSQL startup and migration verification, the next platform step is authentication schema design and implementation.
