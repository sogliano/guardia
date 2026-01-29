Run the test suite for the specified module. If no module is specified, run all tests.

Usage: /test [backend|frontend|all]

Steps:
1. If argument is "backend" or empty: run `cd backend && pytest -v` from the repo root
2. If argument is "frontend" or empty: run `cd frontend && npm run test` from the repo root
3. Report results clearly — number of passed/failed tests
4. If any test fails, read the failing test file and the source code it tests, then propose a fix

Argument: $ARGUMENTS
