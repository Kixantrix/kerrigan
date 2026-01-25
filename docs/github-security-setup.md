# GitHub Repository Security Configuration Guide

This guide provides step-by-step instructions for configuring security settings that must be set manually in GitHub's repository settings.

## Overview

The following security features should be enabled for this public repository but **cannot be configured through code**. They require manual configuration by a repository administrator through GitHub's web interface.

## 🔐 Required Security Settings

### 1. Enable Secret Scanning

**Purpose**: Automatically detects accidentally committed secrets, tokens, and credentials.

**Steps**:
1. Navigate to repository **Settings**
2. Click **Code security and analysis** in the left sidebar
3. Find **Secret scanning**
4. Click **Enable** next to "Secret scanning"

**Why this matters**: Prevents exposure of API keys, passwords, and other sensitive data in your public repository.

**References**:
- [About secret scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)

---

### 2. Enable Push Protection

**Purpose**: Prevents committing secrets by blocking pushes containing detected secrets.

**Steps**:
1. Navigate to repository **Settings**
2. Click **Code security and analysis** in the left sidebar
3. Find **Push protection**
4. Click **Enable** next to "Push protection"

**Why this matters**: Proactively stops secrets from being committed, rather than detecting them after the fact.

**Note**: Push protection requires secret scanning to be enabled first.

**References**:
- [About push protection](https://docs.github.com/en/code-security/secret-scanning/push-protection-for-repositories-and-organizations)

---

### 3. Enable Dependabot Security Updates

**Purpose**: Automatically creates pull requests to update vulnerable dependencies.

**Steps**:
1. Navigate to repository **Settings**
2. Click **Code security and analysis** in the left sidebar
3. Find **Dependabot alerts**
4. Click **Enable** if not already enabled
5. Find **Dependabot security updates**
6. Click **Enable** next to "Dependabot security updates"

**Why this matters**: Keeps dependencies up to date with security patches automatically.

**Optional**: Also enable **Dependabot version updates** for non-security dependency updates
- Create `.github/dependabot.yml` to configure update frequency and ecosystems

**References**:
- [About Dependabot security updates](https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates)
- [Configuring Dependabot version updates](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuring-dependabot-version-updates)

---

### 4. Configure Branch Protection for `main`

**Purpose**: Enforces code review and quality checks before merging to the main branch.

**Steps**:
1. Navigate to repository **Settings**
2. Click **Branches** in the left sidebar under "Code and automation"
3. Click **Add branch protection rule** or **Add rule**
4. Enter `main` in the "Branch name pattern" field
5. Configure the following settings:

#### Required Settings:

**Require a pull request before merging**:
- ✅ Check this option
- Set "Required number of approvals before merging" to **1** (or higher)
- Optional: ✅ "Dismiss stale pull request approvals when new commits are pushed"
- Optional: ✅ "Require review from Code Owners"

**Require status checks to pass before merging**:
- ✅ Check this option
- ✅ "Require branches to be up to date before merging"
- Add status checks:
  - `validate` (from ci.yml workflow)
  - `autonomy_gate` (from agent-gates.yml workflow)
  - Add any other relevant checks from your workflows

**Require conversation resolution before merging**:
- ✅ Check this option (ensures all review comments are addressed)

**Do not allow bypassing the above settings**:
- ✅ "Do not allow bypassing the above settings" (recommended for strict enforcement)
- OR configure specific users/teams who can bypass

**Restrict who can push to matching branches** (Optional but recommended):
- ✅ Check this option
- Add specific users or teams who can push directly to main
- Recommended: Keep this restricted to repository administrators only

#### Optional Settings:

**Require deployments to succeed before merging**:
- Only if you have deployment workflows

**Require signed commits**:
- ✅ Check if you want to enforce commit signing

**Require linear history**:
- ✅ Check if you want to prevent merge commits

**Allow force pushes**:
- ⚠️ Generally keep disabled for main branch

**Allow deletions**:
- ⚠️ Generally keep disabled for main branch

6. Click **Create** or **Save changes**

**Why this matters**: 
- Ensures all code is reviewed before merging
- Enforces CI/CD pipeline success
- Prevents accidental or unauthorized changes to main branch
- Maintains code quality and security standards

**References**:
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)

---

## 🗨️ Optional: Enable GitHub Discussions

**Purpose**: Provides a community forum for Q&A, design discussions, and agent improvement ideas.

**Steps**:
1. Navigate to repository **Settings**
2. Click **General** in the left sidebar
3. Scroll to **Features** section
4. ✅ Check **Discussions**
5. Click **Set up discussions** to initialize

**When to enable**:
- You expect community contributions and want structured discussions
- You want a place for architectural proposals and design discussions
- You want to separate Q&A from issues tracking

**Why consider enabling**:
- Keeps issue tracker focused on actionable items
- Provides better structure for community conversations
- Can have categories like "General", "Ideas", "Q&A", "Show and Tell"

**References**:
- [About discussions](https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/about-discussions)

---

## ✅ Verification Checklist

After configuration, verify the settings are active:

- [ ] Secret scanning is enabled and active
- [ ] Push protection is enabled
- [ ] Dependabot alerts are enabled
- [ ] Dependabot security updates are enabled
- [ ] Branch protection rule exists for `main` branch
- [ ] Required status checks are configured
- [ ] Pull request reviews are required
- [ ] Test the protections by attempting to push directly to main (should be blocked)
- [ ] Verify that PRs require status checks to pass

## 🔍 Monitoring and Maintenance

### Regular Tasks:

1. **Review Dependabot PRs**: Check and merge security update PRs weekly
2. **Check Security Alerts**: Review any secret scanning alerts immediately
3. **Audit Access**: Periodically review who has admin/write access
4. **Review Branch Protection**: Ensure rules haven't been inadvertently modified
5. **Update Status Checks**: Add new required checks as workflows evolve

### Security Dashboard:

- View security overview: Repository → **Security** tab
- Check for alerts: Repository → **Security** → **Dependabot** or **Secret scanning**
- Monitor workflow runs: Repository → **Actions** tab

## 📞 Getting Help

If you encounter issues with these settings:

1. Check [GitHub Documentation](https://docs.github.com/en/code-security)
2. Review [GitHub Community Forums](https://github.community/)
3. Contact GitHub Support if you have a paid plan
4. Open an issue in this repository for Kerrigan-specific questions

---

## 🎯 Quick Reference - All Settings Locations

| Feature | Location | Required |
|---------|----------|----------|
| Secret Scanning | Settings → Code security and analysis | ✅ Yes |
| Push Protection | Settings → Code security and analysis | ✅ Yes |
| Dependabot Alerts | Settings → Code security and analysis | ✅ Yes |
| Dependabot Security Updates | Settings → Code security and analysis | ✅ Yes |
| Branch Protection | Settings → Branches | ✅ Yes |
| Discussions | Settings → General → Features | ⚠️ Optional |

---

**Last Updated**: 2026-01-25

**Note**: GitHub's UI may change over time. If these instructions don't match your interface, check the latest GitHub documentation linked above.
