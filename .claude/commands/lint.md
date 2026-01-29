Run linting and type checking for the specified module.

Usage: /lint [backend|frontend|all]

Steps:
1. If argument is "backend" or empty: run `cd backend && ruff check .` and `cd backend && mypy .`
2. If argument is "frontend" or empty: run `cd frontend && npm run lint`
3. Report all issues found
4. Offer to auto-fix issues where possible (ruff --fix, eslint --fix)

Argument: $ARGUMENTS
