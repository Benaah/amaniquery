---
description: Bootstrap Local Development Environment
---

# Local Development Setup Workflow

This workflow sets up a fresh development environment for the AmaniQuery project, including the Python backend, Next.js frontend, and necessary configuration files.

1. Ensure Python 3.10+ and Node.js 18+ are installed.
2. Clone the repository and navigate to the project root.
3. Run the automated setup script to create the virtual environment, install dependencies, and set up directories:
   ```bash
   python setup.py
   ```
4. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On Linux/Mac: `source venv/bin/activate`
5. If the `.env` file wasn't created automatically, copy the example:
   ```bash
   cp .env.example .env
   ```
   *Note: Open `.env` and configure your API keys (e.g., `MOONSHOT_API_KEY`, `OPENAI_API_KEY`).*
6. Set up the frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```
7. Verify the installation by running the backend API:
   ```bash
   python start_api.py
   ```
8. In a separate terminal, start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```
