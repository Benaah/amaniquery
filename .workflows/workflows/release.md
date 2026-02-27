---
description: Create GitHub Release
---

# Release Workflow

This workflow standardizes the release process for the AmaniQuery platform via GitHub Actions.

1. Ensure all changes for the release are merged into the `master` branch.
2. Draft the version bump based on Semantic Versioning (e.g., `v1.2.0`). Update any configuration files mapping to the version.
3. Commit and tag the release version locally:

   ```bash
   git tag v1.2.0
   ```

4. Push the tag to upstream:

   ```bash
   git push origin v1.2.0
   ```

5. Pushing a tag starting with `v*` automatically triggers the `.github/workflows/release.yml` GitHub Action.
6. The GitHub Action will:
   - Generate a changelog automatically
   - Create a GitHub Release page
   - Build and attach release artifacts
7. Monitor the Actions tab on GitHub to ensure the workflow runs smoothly. Review the drafted release on the GitHub project page once finished.
