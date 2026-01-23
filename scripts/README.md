# Template Branch Maintenance

This directory contains scripts and documentation for maintaining Kerrigan's template branches.

## Overview

Kerrigan offers three template branches in addition to `main`:

1. **template/minimal** - Core framework only
2. **template/with-examples** - Core + 2 curated examples (hello-swarm, hello-api)
3. **template/enterprise** - Core + all examples and tooling

See [../TEMPLATE-BRANCHES.md](../TEMPLATE-BRANCHES.md) for detailed descriptions and usage instructions.

## Initial Setup

To create the template branches for the first time:

```bash
# Run from repository root
./scripts/create-template-branches.sh

# Push the branches to GitHub
git push -u origin template/minimal
git push -u origin template/with-examples
git push -u origin template/enterprise
```

**Note**: You'll need write access to the repository to push branches.

## Maintenance

Template branches should be updated whenever core framework changes are made to `main`. This includes:

- Changes to `.github/agents/` prompts
- Changes to `.github/workflows/` CI/CD
- Changes to `specs/constitution.md` or core specs
- Changes to `tools/validators/`
- Changes to essential documentation

### Sync Process

1. **Make changes on a feature branch** and merge to `main` as usual
2. **After merging**, run the script to recreate template branches:
   ```bash
   ./scripts/create-template-branches.sh
   ```
3. **Force push** the updated template branches:
   ```bash
   git push -f origin template/minimal
   git push -f origin template/with-examples
   git push -f origin template/enterprise
   ```

### What Gets Removed from Each Template

#### All Templates Remove:
- **Investigation artifacts**:
  - `MILESTONE-*.md`
  - `*-VALIDATION.md`
  - `*-SUMMARY.md`
  - `docs/milestone-*.md`
  - `docs/fresh-user-test.md`
  - `docs/test-issue-agent-workflow.md`
  - `docs/AGENT-SPEC-VALIDATION-SUMMARY.md`

- **Agent feedback history**:
  - `feedback/agent-feedback/*.yaml` (except `TEMPLATE.yaml` and `README.md`)

- **Meta-project specs**:
  - `specs/projects/kerrigan/`
  - `specs/kerrigan/agents/`

#### template/minimal Additionally Removes:
- All examples (`examples/`)
- All example project specs (`specs/projects/*` except `_template/` and `_archive/`)

#### template/with-examples Additionally Removes:
- All examples except `hello-swarm` and `hello-api`
- All example project specs except `hello-swarm` and `hello-api`

#### template/enterprise:
- Only removes items in "All Templates Remove" section

## Automation (Future)

Consider setting up a GitHub Action to:
1. Trigger when changes are pushed to `main`
2. Automatically run `create-template-branches.sh`
3. Force push updated template branches
4. Post a comment on the PR that triggered the sync

Example workflow location: `.github/workflows/sync-template-branches.yml`

## Testing Template Branches

Before pushing template branches, test them locally:

```bash
# Create the branches
./scripts/create-template-branches.sh

# Test minimal template
git checkout template/minimal
ls -la examples/  # Should only have README.md
ls -la specs/projects/  # Should only have _template/ and _archive/

# Test with-examples template
git checkout template/with-examples
ls -la examples/  # Should have hello-swarm, hello-api, README.md
ls -la specs/projects/  # Should have _template/, _archive/, hello-swarm/, hello-api/

# Test enterprise template
git checkout template/enterprise
ls -la examples/  # Should have all examples
ls -la  # Should NOT have MILESTONE-*.md files

# Return to main
git checkout main
```

## Troubleshooting

### Branch Already Exists Error

If you get an error that a template branch already exists:
```bash
# Delete the local branch
git branch -D template/minimal

# Re-run the script
./scripts/create-template-branches.sh
```

### Changes Not Appearing

Make sure you're on a branch that has the changes you want to sync:
```bash
# The script creates template branches from your current branch
git checkout main
git pull
./scripts/create-template-branches.sh
```

### Push Rejected

If your push is rejected, use force push (with caution):
```bash
git push -f origin template/minimal
```

**Warning**: Force pushing rewrites history. Only do this for template branches, never for `main` or feature branches.

## Questions?

- See [../TEMPLATE-BRANCHES.md](../TEMPLATE-BRANCHES.md) for user-facing documentation
- See [../docs/FAQ.md](../docs/FAQ.md) for general questions
- Open an issue for problems or suggestions
