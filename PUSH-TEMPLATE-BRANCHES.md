# Manual Steps to Push Template Branches

The template branches have been created locally but need to be pushed to GitHub.

## Current Status

✅ The following branches exist locally and are ready to push:
- `template/minimal` - Core framework only (0 examples)
- `template/with-examples` - Core + 2 examples (hello-swarm, hello-api)
- `template/enterprise` - Core + all 9 examples

✅ All branches verified:
- Investigation artifacts removed (MILESTONE-*.md, etc.)
- Agent feedback history removed (except TEMPLATE.yaml)
- Meta-project specs removed (specs/kerrigan/agents/, specs/projects/kerrigan/)
- Appropriate examples included per template level

## Required Action

Run these commands to push the branches to GitHub:

```bash
# Make sure you're in the repository directory
cd /home/runner/work/kerrigan/kerrigan

# Push all template branches
git push -u origin template/minimal
git push -u origin template/with-examples
git push -u origin template/enterprise
```

## Alternative: Use GitHub Actions Workflow

After this PR is merged, you can use the GitHub Actions workflow to sync template branches:

1. Go to **Actions** tab in GitHub
2. Select **"Sync Template Branches"** workflow
3. Click **"Run workflow"**
4. Select `main` branch
5. Click **"Run workflow"** button

This will automatically:
- Recreate all template branches from main
- Push them to GitHub
- Generate a summary of changes

## Verifying the Branches

After pushing, verify the branches exist on GitHub:
- https://github.com/Kixantrix/kerrigan/tree/template/minimal
- https://github.com/Kixantrix/kerrigan/tree/template/with-examples
- https://github.com/Kixantrix/kerrigan/tree/template/enterprise

## Future Maintenance

To update template branches after making changes to main:

```bash
# Option 1: Use the script
./scripts/create-template-branches.sh
git push -f origin template/minimal template/with-examples template/enterprise

# Option 2: Use GitHub Actions (after enabling auto-sync)
# Edit .github/workflows/sync-template-branches.yml to uncomment the push trigger
```

See `scripts/README.md` for detailed maintenance instructions.
