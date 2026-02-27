---
description: Run CI Checks Locally
---

# Local CI Checks Workflow

This workflow replicates the GitHub Actions CI pipeline locally to ensure code quality before pushing.

1. Activate your Python virtual environment if not already active.
2. Run code formatting checks (Black):
   // turbo

   ```bash
   black --check --diff .
   ```

   *(To fix formatting issues automatically, run `black .`)*
3. Run Python linting (Flake8):
   // turbo

   ```bash
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
   ```

4. Run Python static type checking (mypy):
   // turbo

   ```bash
   mypy . --ignore-missing-imports
   ```

5. Run the frontend linter:
   // turbo

   ```bash
   cd frontend
   npm run lint
   cd ..
   ```

6. Run the frontend TypeScript type check:
   // turbo

   ```bash
   cd frontend
   npx tsc --noEmit
   cd ..
   ```

7. Verify Docker Compose configuration syntax:
   // turbo

   ```bash
   docker-compose -f docker-compose.yml config
   ```
