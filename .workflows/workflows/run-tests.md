---
description: Run Full Test Suite
---

# Test Execution Workflow

This workflow covers running the automated test suites for the API, Frontend, and Android applications locally.

1. Ensure your local development services (Database, Redis, etc.) are running if the tests depend on them:

   ```bash
   make dev
   ```

2. Run the **Python Backend** test suite using pytest with coverage:
   // turbo

   ```bash
   pytest --cov=. --cov-report=xml --cov-report=term-missing -v
   ```

   *To run a specific test file: `pytest tests/unit/test_module1.py -v`*
3. Run the **API tests** inside the Docker container (if running via Docker Compose):
   // turbo

   ```bash
   make test-api
   ```

4. Run the **Next.js Frontend** tests:
   // turbo

   ```bash
   cd frontend
   npm run test
   cd ..
   ```

   *(Or via Docker: `make test-frontend`)*
5. Run the **Android App** tests (Jest):
   // turbo

   ```bash
   cd android-app
   npm test -- --coverage --watchAll=false
   cd ..
   ```

6. Review the test results and coverage reports generated.
