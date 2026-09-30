# Database Migration Guide

JeevanMitra 2.0 uses Alembic for database migrations and supports both SQLite (for local development/testing) and PostgreSQL (for staging/production).

## Environment Setup

Configure your database connection string in `.env`:

```env
# Local development (SQLite)
DATABASE_URL=sqlite:///./jeevanmitra.db

# Staging / Production (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/jeevanmitra
```

## Running Migrations

Never use `create_all()` in production. Always apply the database schema via Alembic.

**Apply all pending migrations (Upgrade to Head):**
```bash
alembic upgrade head
```

## Creating New Migrations

When you change the data model, create a new migration script:
```bash
alembic revision -m "description_of_changes"
```
Then, edit the generated script in `alembic/versions/` to include the `op.execute()` or other alembic commands.

## Rollback

To rollback the last migration:
```bash
alembic downgrade -1
```

To rollback to a specific revision:
```bash
alembic downgrade <revision_id>
```

## Migrating from SQLite to PostgreSQL

If you have an existing SQLite database (e.g. from the prototype phase) and want to move its data to a new PostgreSQL instance:

1. Ensure the PostgreSQL instance is empty and fully migrated to `head`.
2. Run the idempotent data migration script:
```bash
python backend/scripts/migrate_sqlite_to_postgres.py --sqlite-db ./jeevanmitra.db
```

The script will:
- Connect to your Postgres instance defined in `DATABASE_URL`.
- Migrate records in strict dependency order (e.g. parent tables before child tables).
- Validate counts and preserve foreign-key integrity.
