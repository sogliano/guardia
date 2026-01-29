Create and run database migrations.

Usage: /migrate [create "description"|run|status]

Steps:
1. If "create": run `cd backend && alembic revision --autogenerate -m "description"`
2. If "run" or empty: run `cd backend && alembic upgrade head`
3. If "status": run `cd backend && alembic current` and `cd backend && alembic history --verbose -3`
4. Report the migration state

Argument: $ARGUMENTS
