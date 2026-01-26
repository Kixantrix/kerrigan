# Upgrading Satellite Kerrigan Installations

## Overview

This playbook guides you through upgrading a satellite Kerrigan installation (a repository created from the Kerrigan template) with the latest improvements from the main Kerrigan repository.

**Target audience**: Project maintainers managing satellite installations of Kerrigan.

**Related documents**:
- [TEMPLATE-BRANCHES.md](../TEMPLATE-BRANCHES.md) - Available template branches
- [CHANGELOG.md](../CHANGELOG.md) - Version history and breaking changes
- [playbooks/replication-guide.md](replication-guide.md) - Setting up new installations

## When to Upgrade

Consider upgrading when:

**New features available**:
- Improved agent prompts with better instructions
- Enhanced validators for quality enforcement
- New workflows for automation
- Additional playbooks or skills

**Bug fixes released**:
- Security vulnerabilities patched
- CI/CD workflow fixes
- Validator improvements

**Breaking changes announced**:
- Major version updates requiring migration
- Deprecated features being removed
- New requirements or dependencies

**Periodic maintenance**:
- Quarterly reviews of main repo changes
- Before starting major new projects
- After completing project milestones

## Pre-Upgrade Checklist

Before upgrading, ensure:

- [ ] **Clean working directory** - Commit or stash all local changes
- [ ] **Review CHANGELOG** - Read the [CHANGELOG.md](../CHANGELOG.md) for breaking changes
- [ ] **Backup important customizations** - Note any project-specific modifications
- [ ] **Test environment ready** - Have a way to test after upgrade
- [ ] **Team notification** - Inform team members of planned upgrade

## Upgrade Methods

### Method 1: Automated Upgrade Script (Recommended)

Use the provided PowerShell script for selective component upgrades.

**Prerequisites**:
- Git installed and configured
- PowerShell 5.1+ (Windows) or PowerShell Core 7+ (cross-platform)
- Write access to your repository

**Step 1: Check current version**

```powershell
# View your current Kerrigan version
Get-Content kerrigan-version.json | ConvertFrom-Json
```

**Step 2: Preview changes**

```powershell
# See what would change without applying
./tools/upgrade-kerrigan.ps1 -DryRun

# Show detailed diff for all components
./tools/upgrade-kerrigan.ps1 -ShowDiff
```

**Step 3: Selective upgrade**

Upgrade specific components:

```powershell
# Upgrade only workflows and prompts
./tools/upgrade-kerrigan.ps1 -Components workflows,prompts

# Upgrade only validators
./tools/upgrade-kerrigan.ps1 -Components validators

# Upgrade all components
./tools/upgrade-kerrigan.ps1 -Components all
```

**Step 4: Review and commit**

```powershell
# Review changes
git diff

# Test your project
# (run your tests, linters, builds)

# Commit the upgrade
git add .
git commit -m "Upgrade Kerrigan to version X.Y.Z"
git push
```

### Method 2: Manual Selective Cherry-Pick

For fine-grained control, manually cherry-pick specific changes.

**Step 1: Add upstream remote**

```bash
# Add main Kerrigan repo as upstream
git remote add kerrigan-upstream https://github.com/Kixantrix/kerrigan
git fetch kerrigan-upstream main
```

**Step 2: Identify changes**

```bash
# See what changed in specific paths
git log --oneline HEAD..kerrigan-upstream/main -- .github/workflows
git log --oneline HEAD..kerrigan-upstream/main -- .github/agents
git log --oneline HEAD..kerrigan-upstream/main -- tools/validators

# View specific file changes
git diff kerrigan-upstream/main -- .github/workflows/ci.yml
```

**Step 3: Cherry-pick commits**

```bash
# Cherry-pick specific commits
git cherry-pick <commit-hash>

# Or checkout specific files
git checkout kerrigan-upstream/main -- .github/workflows/ci.yml
git checkout kerrigan-upstream/main -- .github/agents/swe.md
```

**Step 4: Resolve conflicts**

If conflicts occur:

```bash
# Review conflict markers in files
git status

# Manually edit conflicted files
# Keep your customizations where appropriate

# Mark as resolved
git add <resolved-file>
git cherry-pick --continue
```

**Step 5: Update version manifest**

Manually update `kerrigan-version.json`:

```json
{
  "version": "X.Y.Z",
  "last_updated": "2026-01-25T20:00:00Z",
  "components": {
    "workflows": "X.Y.Z",
    "prompts": "X.Y.Z"
  }
}
```

### Method 3: Template Branch Merge

Merge from specific template branches for major upgrades.

**Step 1: Identify your template**

Determine which template you started from:
- `template/minimal` - Core framework only
- `template/with-examples` - Core + examples
- `template/enterprise` - Full featured

**Step 2: Fetch template updates**

```bash
# Fetch the template branch
git fetch kerrigan-upstream template/minimal
# Or your specific template
```

**Step 3: Merge carefully**

```bash
# Create a backup branch first
git checkout -b pre-upgrade-backup

# Return to main
git checkout main

# Merge with strategy
git merge kerrigan-upstream/template/minimal --no-commit

# Review what will be merged
git status
git diff --cached
```

**Step 4: Resolve conflicts strategically**

For each conflict:

- **Keep upstream** for: Core workflows, validators, prompts
- **Keep yours** for: Project-specific configs, custom workflows
- **Merge both** for: Documentation (combine sections)

**Step 5: Complete and test**

```bash
# Complete the merge
git commit -m "Merge template/minimal updates"

# Test thoroughly
# Run all tests, builds, validators

# Push when confident
git push
```

## Component-Specific Upgrade Notes

### Workflows (`.github/workflows/`)

**What changes**:
- CI validation improvements
- New automation workflows
- Performance optimizations

**Customization tips**:
- Keep custom workflows in separate files prefixed with `custom-`
- Review CI changes for new required labels or settings
- Test CI pipeline on a feature branch first

**Post-upgrade testing**:
```bash
# Trigger CI manually
git push origin feature/test-ci-upgrade

# Verify validators run
# Check GitHub Actions logs
```

### Prompts (`.github/agents/`)

**What changes**:
- Improved agent instructions
- Better examples and guidelines
- New agent roles

**Customization tips**:
- Document any prompt modifications in a separate file
- Consider merging improvements with your customizations
- Test agents on small tasks first

**Post-upgrade testing**:
- Run agent auditing: `python tools/agent_audit.py`
- Create test issue and assign to agent
- Verify agent behavior meets expectations

### Validators (`tools/validators/`)

**What changes**:
- New validation rules
- Bug fixes in existing validators
- Performance improvements

**Customization tips**:
- Custom validators should be in separate files
- Update CI if validators add new checks
- Review validator output format changes

**Post-upgrade testing**:
```bash
# Run validators manually
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py

# Verify they pass on your project
```

### Playbooks (`playbooks/`)

**What changes**:
- New best practices
- Enhanced workflows
- Additional examples

**Customization tips**:
- Playbooks are documentation; safe to merge
- Add project-specific playbooks separately
- Reference upstream playbooks in custom docs

**Post-upgrade testing**:
- Review new playbooks for applicability
- Update team documentation if needed

### Skills (`skills/`)

**What changes**:
- New reusable patterns
- Updated examples
- Additional skills libraries

**Customization tips**:
- Add project-specific skills in separate files
- Skills are reference material; safe to merge
- Index new skills in your project docs

**Post-upgrade testing**:
- Review new skills for project relevance
- Update agent instructions to reference new skills

## Handling Conflicts

### Conflict Resolution Strategy

**1. Identify conflict type**:
- **Core vs. Custom**: Upstream changed a file you customized
- **Version Skew**: Both changed the same functionality
- **Structural**: File organization changed

**2. Resolution approaches**:

**Keep upstream** for:
```
# Files you rarely customize
.github/workflows/ci.yml
tools/validators/*.py
```

**Keep yours** for:
```
# Project-specific files
.github/workflows/custom-*.yml
specs/projects/*
status.json
```

**Merge carefully** for:
```
# Files with both core and custom content
.github/agents/*.md (if you added examples)
playbooks/*.md (if you added sections)
README.md (preserve project-specific changes)
```

**3. Testing after conflicts**:
- Run all validators
- Test CI pipeline
- Review agent behavior
- Check documentation links

### Common Conflict Scenarios

**Scenario 1: CI Workflow Updated**

```yaml
# Conflict in .github/workflows/ci.yml
<<<<<<< HEAD
- name: Custom validation
  run: python custom-validator.py
=======
- name: Improved artifact check
  run: python tools/validators/check_artifacts.py --strict
>>>>>>> kerrigan-upstream/main
```

**Resolution**: Keep both if compatible

```yaml
- name: Improved artifact check
  run: python tools/validators/check_artifacts.py --strict
- name: Custom validation
  run: python custom-validator.py
```

**Scenario 2: Agent Prompt Enhanced**

```markdown
<<<<<<< HEAD
## Custom Instructions
Always use our coding style guide.
=======
## Updated Best Practices
Follow these enhanced patterns:
1. ...
>>>>>>> kerrigan-upstream/main
```

**Resolution**: Combine both sections

```markdown
## Updated Best Practices
Follow these enhanced patterns:
1. ...

## Project-Specific Instructions
Always use our coding style guide.
```

## Post-Upgrade Validation

### Immediate Checks

**1. Version manifest updated**:
```powershell
Get-Content kerrigan-version.json
# Verify version and components are updated
```

**2. Git status clean**:
```bash
git status
# Should show no untracked files or unexpected changes
```

**3. Basic structure intact**:
```bash
# Verify key files exist
test -f .github/workflows/ci.yml && echo "CI: OK"
test -f tools/validators/check_artifacts.py && echo "Validators: OK"
test -d .github/agents && echo "Agents: OK"
```

### Functional Testing

**Run validators**:
```bash
# Test artifact validation
python tools/validators/check_artifacts.py

# Test quality bar
python tools/validators/check_quality_bar.py

# Test PR documentation
python tools/validators/check_pr_documentation.py
```

**Run CI locally** (if possible):
```bash
# Using act or similar
act -j validate

# Or trigger on feature branch
git checkout -b test-upgrade
git push origin test-upgrade
# Watch GitHub Actions
```

**Test agent workflow**:
1. Create a small test issue
2. Add `agent:go` label
3. Assign to agent
4. Verify agent uses updated prompts

### Breaking Changes Checklist

After upgrading, check for breaking changes:

- [ ] **New required labels** - Check if CI needs new labels
- [ ] **Validator strictness** - Verify existing artifacts pass
- [ ] **Workflow requirements** - Check for new CI requirements
- [ ] **Agent prompt changes** - Test agent behavior on known tasks
- [ ] **File structure** - Verify no required files were moved/renamed
- [ ] **Dependencies** - Check if new Python packages needed

## Rollback Procedure

If upgrade causes issues:

**Option 1: Revert commit**
```bash
# If not pushed yet
git reset --hard HEAD~1

# If already pushed
git revert <commit-hash>
git push
```

**Option 2: Restore from backup branch**
```bash
# Create backup before upgrade
git checkout -b pre-upgrade-backup

# After problems, restore
git checkout main
git reset --hard pre-upgrade-backup
git push --force  # Use with caution
```

**Option 3: Selective rollback**
```bash
# Revert specific files
git checkout HEAD~1 -- .github/workflows/ci.yml
git commit -m "Rollback CI workflow"
```

## Upgrade Frequency

### Recommended Schedule

**Critical updates**: Immediately
- Security vulnerabilities
- Critical bug fixes
- Breaking changes affecting your workflow

**Feature updates**: Monthly
- New workflows or automations
- Enhanced agent prompts
- New validators or tools

**Full version updates**: Quarterly
- Major version bumps (2.0.0, 3.0.0)
- Comprehensive testing
- Team training on new features

**Stay informed**:
- Watch the [main repository](https://github.com/Kixantrix/kerrigan) for releases
- Subscribe to release notifications
- Review [CHANGELOG.md](../CHANGELOG.md) regularly

## Troubleshooting

### Issue: Script fails with "Not a git repository"

**Cause**: Not running from repository root

**Solution**:
```bash
cd /path/to/your/project
./tools/upgrade-kerrigan.ps1
```

### Issue: "Uncommitted changes" error

**Cause**: Working directory not clean

**Solution**:
```bash
# Stash changes
git stash

# Run upgrade
./tools/upgrade-kerrigan.ps1

# Restore changes
git stash pop
```

### Issue: Upstream remote already exists with different URL

**Cause**: Previously configured upstream

**Solution**:
```bash
# Update remote URL
git remote set-url kerrigan-upstream https://github.com/Kixantrix/kerrigan

# Or remove and re-add
git remote remove kerrigan-upstream
git remote add kerrigan-upstream https://github.com/Kixantrix/kerrigan
```

### Issue: Merge conflicts in every file

**Cause**: Starting from very old version or heavy customization

**Solution**:
- Use selective cherry-pick instead of full merge
- Upgrade one component at a time
- Consider manual file-by-file review

### Issue: CI fails after upgrade

**Cause**: New validators or changed requirements

**Solution**:
1. Read error messages carefully
2. Check CHANGELOG for breaking changes
3. Update project structure as needed
4. Review validator documentation
5. Ask for help in issue tracker

## Best Practices

### Before Upgrading

1. **Read the CHANGELOG** - Understand what's changing
2. **Backup your work** - Create a branch or tag
3. **Start small** - Upgrade one component first
4. **Test incrementally** - Don't upgrade everything at once

### During Upgrade

1. **Review diffs carefully** - Understand each change
2. **Preserve customizations** - Document what you keep
3. **Test frequently** - Validate after each component
4. **Document decisions** - Note why you kept/changed things

### After Upgrade

1. **Run full test suite** - Ensure nothing broke
2. **Update documentation** - Reflect any changes
3. **Train team** - Share new features/changes
4. **Monitor closely** - Watch for issues in first week

### Maintaining Compatibility

1. **Minimize customizations** - Less to conflict with
2. **Use extension points** - Custom workflows in separate files
3. **Document deviations** - Track where you differ from upstream
4. **Regular small updates** - Easier than big jumps

## Getting Help

If you encounter issues during upgrade:

**Documentation**:
- Check [CHANGELOG.md](../CHANGELOG.md) for known issues
- Review [FAQ.md](../docs/FAQ.md) for common questions
- Read component-specific documentation

**Community**:
- Open issue in [main repository](https://github.com/Kixantrix/kerrigan/issues)
- Tag issues with `upgrade`, `satellite-installation`
- Provide version info and error messages

**Self-help**:
- Compare your files with upstream using `git diff`
- Check GitHub Actions logs for CI failures
- Test on a separate branch first

## Examples

### Example 1: Upgrading Workflows Only

```powershell
# Check what would change
./tools/upgrade-kerrigan.ps1 -Components workflows -ShowDiff

# Apply upgrade
./tools/upgrade-kerrigan.ps1 -Components workflows

# Test CI
git add .github/workflows
git commit -m "Upgrade workflows to v1.1.0"
git push origin feature/upgrade-workflows

# Verify CI passes, then merge to main
```

### Example 2: Upgrading from 1.0.0 to 2.0.0

```powershell
# Read CHANGELOG for breaking changes
Get-Content CHANGELOG.md | Select-String "## \[2.0.0\]" -Context 0,30

# Preview all changes
./tools/upgrade-kerrigan.ps1 -DryRun

# Backup current state
git checkout -b v1.0.0-backup

# Return to main and upgrade
git checkout main
./tools/upgrade-kerrigan.ps1 -Components all

# Review changes thoroughly
git diff

# Test everything
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py
# Run your project tests

# Commit and push
git add .
git commit -m "Upgrade Kerrigan from v1.0.0 to v2.0.0"
git push
```

### Example 3: Selective File Upgrade

```bash
# Just want the latest SWE agent prompt
git remote add kerrigan-upstream https://github.com/Kixantrix/kerrigan
git fetch kerrigan-upstream main

# Check what changed
git diff kerrigan-upstream/main -- .github/agents/swe.md

# Apply if good
git checkout kerrigan-upstream/main -- .github/agents/swe.md
git commit -m "Update SWE agent prompt to latest"

# Update version manifest
# Edit kerrigan-version.json to reflect prompts version
git add kerrigan-version.json
git commit -m "Update version manifest"
```

## Related Resources

- [TEMPLATE-BRANCHES.md](../TEMPLATE-BRANCHES.md) - Template options
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [playbooks/replication-guide.md](replication-guide.md) - New installations
- [docs/setup.md](../docs/setup.md) - Initial setup
