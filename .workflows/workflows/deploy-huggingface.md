---
description: Deploy to HuggingFace Spaces
---

# HuggingFace Spaces Deployment Workflow

This workflow encapsulates the process for deploying the AmaniQuery platform to HuggingFace Spaces.

1. Ensure that your local environment has the `HF_TOKEN` configured.
2. Verify the `Dockerfile.huggingface` handles the build optimizations successfully locally if needed:

   ```bash
   docker build -t test-hf-build -f Dockerfile.huggingface .
   ```

3. Run the deployment script targeting HuggingFace:
   // turbo

   ```bash
   ./scripts/build_and_deploy.sh hf
   ```

4. Since HuggingFace Spaces run via `uvicorn Module4_NiruAPI.api:app --host 0.0.0.0 --port 7860`, monitor the HuggingFace UI for build logs.
5. If deployment fails, inspect the `deploy_to_hf.py` script output. Ensure the required HuggingFace dataset/secrets are set in your Space's settings.
6. Verify the `/health` endpoint of your deployed Space via curl or a browser.
