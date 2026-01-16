# Triage Playbook

This playbook documents triage workflows and decision trees for managing the PR review pipeline in Kerrigan.

## Overview

The triage role is responsible for maintaining a healthy PR pipeline by:
- Reviewing incoming PRs for quality and completeness
- Managing CI status and resolving build/test failures
- Approving quality work and merging PRs
- Restarting stalled agents
- Creating follow-up issues from review findings
- Maintaining visibility into PR pipeline health

## Quick Start

```powershell
# View PR triage dashboard
./tools/triage-prs.ps1

# View all issues
./tools/show-issues.ps1

# Systematic PR review (add Copilot as reviewer)
./tools/review-prs.ps1
```

## Standard Review Cycle

### 1. Check PR Pipeline Status

```powershell
./tools/triage-prs.ps1
```

This shows PRs in priority order:
1. 🟢 **Merge ready** - Approved, CI passing, no conflicts
2. 🔴 **CI failures** - Need investigation/fixes
3. ⚠️ **Merge conflicts** - Need rebase
4. ⏸️ **Stalled drafts** - Agent may need restart
5. 📋 **Ready for review** - Awaiting human review

### 2. Handle Merge-Ready PRs (Highest Priority)

For PRs that are approved, CI passing, and have no conflicts:

```bash
# View the PR one more time
gh pr view <PR#>

# Merge with squash (recommended for most PRs)
gh pr merge <PR#> --squash

# Or merge with regular merge (for meaningful commit history)
gh pr merge <PR#> --merge
```

**Decision tree for merge strategy:**
- Use **squash merge** when:
  - PR has many small commits
  - Commit messages aren't meaningful
  - Want clean main branch history
  - Default choice for most PRs
  
- Use **regular merge** when:
  - PR has meaningful, well-structured commits
  - Commit history tells a story
  - Want to preserve individual commits
  - Rare cases only

### 3. Review PRs Ready for Review

For each PR marked ready for review:

#### Step 1: Check Completeness
- ✅ Links to project folder (`specs/projects/<name>/`)
- ✅ References specific milestone or task
- ✅ Has clear description of changes
- ✅ Includes rationale for approach taken

If missing any of these, comment requesting the information.

#### Step 2: Verify Tests
- ✅ Tests added or updated
- ✅ Test coverage adequate for changes
- ✅ All tests passing in CI

If tests are missing:
```bash
gh pr comment <PR#> --body "Please add tests for the new functionality, or provide rationale if tests aren't applicable."
```

#### Step 3: Check Documentation
- ✅ Documentation updated per artifact contracts
- ✅ README updated if user-facing changes
- ✅ Comments added for complex logic (if applicable)

If documentation is missing:
```bash
gh pr comment <PR#> --body "Please update documentation to reflect the changes. See playbooks/pr-review.md for requirements."
```

#### Step 4: Review Code Quality
- ✅ Code follows project conventions
- ✅ No obvious bugs or issues
- ✅ Files under quality bar limits (800 LOC)
- ✅ Well-structured and readable

If quality issues found:
```bash
gh pr review <PR#> --request-changes --body "Issues found:
- <issue 1>
- <issue 2>

Please address these and mark ready for review again."
```

#### Step 5: Verify CI Status
- ✅ All CI checks passing
- ✅ No validator failures
- ✅ No merge conflicts

Check CI status:
```bash
gh pr checks <PR#>
```

#### Step 6: Approve if All Checks Pass

If everything looks good:
```bash
gh pr review <PR#> --approve --body "Excellent work! 🎉

Strengths:
- Clear, well-structured implementation
- Comprehensive test coverage
- All CI checks passing
- Follows project conventions

Ready to merge! ✅"
```

### 4. Handle CI Failures

#### Step 1: Identify Root Cause

```bash
# View CI status
gh pr checks <PR#>

# View failed check logs
gh run view <RUN_ID> --log-failed
```

Common failure types:
- **Validator failures** - check_artifacts.py, check_quality_bar.py, etc.
- **Test failures** - Unit tests, integration tests
- **Linting failures** - Code style violations
- **Build failures** - Compilation errors
- **Permission issues** - Workflow doesn't have required permissions

#### Step 2: Determine Fix Strategy

**For validator failures:**
1. Check if failure is legitimate (actual quality issue)
2. If legitimate, comment on PR requesting fix
3. If false positive, update validator script or add exception

**For test failures:**
1. Comment on PR notifying author
2. If test is flaky, investigate and fix test
3. If test reveals bug, create follow-up issue

**For build/lint failures:**
1. Comment on PR notifying author
2. If systemic issue (missing dependency), fix in CI config

**For permission issues:**
1. Update workflow YAML to add required permissions
2. Retrigger CI

#### Step 3: Fix and Retrigger

**Fix CI configuration:**
```bash
# Edit workflow file
code .github/workflows/ci.yml

# Commit and push
git add .github/workflows/ci.yml
git commit -m "Fix CI: <description>"
git push
```

**Retrigger CI on PR:**
```bash
# Re-run failed checks
gh run rerun <RUN_ID>

# Or close/reopen PR (for bot PRs)
gh pr close <PR#>
gh pr reopen <PR#>
```

#### Step 4: Monitor Resolution

Check back after CI completes:
```bash
gh pr checks <PR#>
```

### 5. Handle Merge Conflicts

For PRs with merge conflicts:

```bash
# Notify author
gh pr comment <PR#> --body "This PR has merge conflicts with main. Please rebase:

\`\`\`bash
git checkout <branch-name>
git fetch origin
git rebase origin/main
git push --force-with-lease
\`\`\`

Let me know if you need help with the rebase."
```

If author is unable to rebase (e.g., bot PR), you may need to do it manually:
```bash
# Checkout PR branch
gh pr checkout <PR#>

# Rebase on main
git rebase origin/main

# Resolve conflicts (if any)
# Edit files, then:
git add .
git rebase --continue

# Force push
git push --force-with-lease
```

### 6. Restart Stalled Agents

For draft PRs with no activity for >24 hours:

```bash
# Comment to restart agent
gh pr comment <PR#> --body "@copilot Please continue work on this PR. Review the task requirements and complete remaining work."
```

If agent doesn't respond after another 24 hours:
```bash
# Check PR for issues
gh pr view <PR#>

# May need manual rebase if agent hit sandboxing limits
gh pr checkout <PR#>
git rebase origin/main
git push --force-with-lease

# Comment again
gh pr comment <PR#> --body "@copilot Please continue. I've rebased this PR on main."
```

### 7. Create Follow-up Issues

When you identify gaps or improvements during review that shouldn't block the PR:

```bash
gh issue create \
  --title "Follow-up: <description>" \
  --body "## Context

Discovered during review of PR #<PR#>

## Problem

<Describe the gap or issue>

## Proposed Solution

<Suggest approach>

## Acceptance Criteria

- [ ] <criterion 1>
- [ ] <criterion 2>

## References

- Related PR: #<PR#>" \
  --label "role:swe,agent:go"
```

## CI Troubleshooting Decision Tree

```
CI Failure Detected
  │
  ├─ Validator Failure?
  │    ├─ Legitimate issue → Comment on PR requesting fix
  │    └─ False positive → Update validator or add exception
  │
  ├─ Test Failure?
  │    ├─ New bug → Comment on PR, create follow-up issue
  │    ├─ Flaky test → Investigate and fix test
  │    └─ Expected failure → Check if PR is WIP
  │
  ├─ Build/Lint Failure?
  │    ├─ Code issue → Comment on PR requesting fix
  │    └─ Config issue → Fix CI configuration
  │
  └─ Permission Issue?
       └─ Update workflow permissions
```

## PR Review Decision Tree

```
PR Ready for Review
  │
  ├─ Completeness Check
  │    ├─ Missing context? → Request information
  │    └─ Complete → Continue
  │
  ├─ Test Coverage Check
  │    ├─ No tests? → Request tests or rationale
  │    ├─ Tests failing? → Request fixes
  │    └─ Tests passing → Continue
  │
  ├─ Documentation Check
  │    ├─ Docs missing? → Request updates
  │    └─ Docs updated → Continue
  │
  ├─ Code Quality Check
  │    ├─ Quality issues? → Request changes
  │    └─ Quality good → Continue
  │
  ├─ CI Status Check
  │    ├─ CI failing? → See CI Troubleshooting
  │    ├─ CI pending? → Wait for completion
  │    └─ CI passing → Continue
  │
  └─ Merge Conflicts Check
       ├─ Has conflicts? → Request rebase
       └─ No conflicts → APPROVE & MERGE
```

## Agent Recovery Decision Tree

```
Draft PR Stalled (>24h)
  │
  ├─ Comment to restart agent
  │    └─ Wait 24 hours
  │         │
  │         ├─ Agent responds? → Monitor progress
  │         │
  │         └─ No response?
  │              ├─ Check for sandboxing issues
  │              ├─ Manual rebase if needed
  │              ├─ Comment again
  │              └─ Wait 24 hours
  │                   │
  │                   ├─ Agent responds? → Monitor progress
  │                   │
  │                   └─ Still no response?
  │                        ├─ Check rate limiting
  │                        ├─ Check for blocking errors
  │                        └─ Escalate to manual completion
```

## Quality Checklist

Before approving any PR, verify:

### Required Elements
- [ ] Links to project folder (`specs/projects/<name>/`)
- [ ] References specific milestone or task
- [ ] Tests added or updated (or rationale provided)
- [ ] Documentation updated per artifact contracts

### CI & Mergeability
- [ ] All CI checks passing
- [ ] All validators passing
- [ ] No merge conflicts
- [ ] No blocking review comments

### Code Quality
- [ ] Code follows project conventions
- [ ] Files under quality bar limits (800 LOC, or has allow:large-file label)
- [ ] No obvious bugs or security issues
- [ ] Well-structured and readable code

### Testing
- [ ] Unit tests present
- [ ] Integration tests if applicable
- [ ] Edge cases covered
- [ ] Manual verification performed (if applicable)

### Documentation
- [ ] README updated if needed
- [ ] API docs updated if needed
- [ ] Comments added for complex logic
- [ ] PR description clearly explains changes

## Approval Comment Templates

### Template 1: Excellent Implementation
```
Excellent work on this feature! 🎉

Strengths:
- Clear, well-structured implementation following the architecture
- Comprehensive test coverage with unit and integration tests
- All files under quality bar limits
- Clean commit history and clear PR description
- Manual verification performed and documented

All CI checks passing. Ready to merge! ✅
```

### Template 2: Good Work with Suggestions
```
Great implementation! A few suggestions for future PRs:

Strengths:
- Solid implementation following the plan
- Good test coverage
- CI passing

Suggestions for next time:
- Consider breaking large functions into smaller, focused ones
- Add more inline comments for complex logic
- Include manual verification results in PR description

Approved! ✅
```

### Template 3: Changes Requested
```
Thanks for the PR! I've identified a few issues that need to be addressed:

Issues:
- [ ] CI failing: test_integration.py has 2 failing tests
- [ ] Missing tests for error handling in auth.py
- [ ] file_handler.py is 912 lines (exceeds 800 LOC quality bar)
- [ ] No link to project folder in PR description

Please address these issues and mark ready for review again.

Guidelines:
- See playbooks/pr-review.md for PR requirements
- See specs/kerrigan/030-quality-bar.md for quality standards
- Run validators locally: python tools/validators/check_quality_bar.py
```

## Common Scenarios & Solutions

### Scenario 1: Multiple PRs with Same CI Failure

**Symptoms:** Several PRs failing with same error

**Solution:**
1. Identify the common cause (likely CI config or validator change)
2. Fix the root cause (update workflow, fix validator)
3. Comment on all affected PRs explaining the fix
4. Retrigger CI on all affected PRs

```bash
# Fix the root cause
code .github/workflows/ci.yml
git commit -am "Fix CI: <description>"
git push

# Notify affected PRs
for pr in 123 124 125; do
  gh pr comment $pr --body "CI issue has been fixed. Retriggering checks."
done
```

### Scenario 2: PR Approved but CI Fails After Rebase

**Symptoms:** PR was approved, then rebased, now CI failing

**Solution:**
1. Check what changed during rebase
2. If legitimate failure, un-approve and request fixes
3. Don't merge until CI passes again

```bash
# View PR again
gh pr view <PR#>

# Check CI logs
gh pr checks <PR#>

# Comment requesting fix
gh pr comment <PR#> --body "CI is now failing after the rebase. Please review the failures and fix."
```

### Scenario 3: Large PR (>1000 LOC)

**Symptoms:** PR has many lines of changes

**Solution:**
1. Check if it's one large file or many small files
2. If one large file, check for quality bar violation
3. If multiple files under limit, that's acceptable
4. Suggest splitting into multiple PRs for future

```bash
# Check file sizes
gh pr diff <PR#> | grep "^diff --git" -A 5

# If quality bar violation without allow:large-file label
gh pr comment <PR#> --body "This PR modifies large files (>800 LOC). Please either:
1. Add allow:large-file label with justification, or
2. Refactor into smaller, focused modules"
```

### Scenario 4: Bot PR Needs CI Retrigger

**Symptoms:** Bot PR has CI failure that looks like it should be retriggered

**Solution:**
1. Check if bot can retrigger itself (usually not)
2. Close and reopen PR to retrigger
3. Or manually rerun the workflow

```bash
# Option 1: Close and reopen
gh pr close <PR#>
gh pr reopen <PR#>

# Option 2: Rerun workflow
gh run rerun <RUN_ID>
```

### Scenario 5: Draft PR from Human Author

**Symptoms:** Draft PR from non-bot author, not progressing

**Solution:**
1. Check if author intended it to be draft
2. Comment asking if ready for review
3. Offer to mark as ready if author confirms

```bash
gh pr comment <PR#> --body "Hi @<author>! Is this PR ready for review, or still work in progress? Let me know if you'd like me to mark it as ready for review."
```

## Integration with Other Tools

### Validators
Run validators locally before approving:
```bash
python tools/validators/check_artifacts.py
python tools/validators/check_quality_bar.py
python tools/validators/check_pr_documentation.py
```

### Agent Audit
Verify agent signatures in PRs:
```bash
# Check if PR has valid agent signature
python tools/agent_audit.py validate-pr pr_body.txt

# Generate signature for triage work
python tools/agent_audit.py create-signature role:triage
```

### Issue Tracking
Monitor related issues:
```bash
# View all open issues
./tools/show-issues.ps1

# View issues for specific project
./tools/show-issues.ps1 | grep "project-name"
```

## Metrics to Track

### Daily Metrics
- Number of PRs merged
- Number of PRs reviewed
- Average time to review
- Number of CI failures resolved

### Weekly Metrics
- PR pipeline health (% passing CI)
- Average time to merge (from creation to merge)
- Number of stalled PRs restarted
- Number of follow-up issues created

### Quality Metrics
- % of PRs passing review on first attempt
- % of PRs meeting quality bar
- % of PRs with adequate tests
- % of PRs with proper documentation

## Best Practices

1. **Review promptly** - Aim to review new PRs within 24 hours
2. **Be thorough** - Check all quality criteria before approving
3. **Provide feedback** - Highlight strengths and areas for improvement
4. **Create follow-ups** - Don't block PRs on minor issues; create follow-up issues
5. **Monitor CI** - Check CI status regularly and fix systemic issues
6. **Restart agents proactively** - Don't wait too long to restart stalled agents
7. **Merge regularly** - Merge approved PRs promptly to keep pipeline flowing
8. **Document decisions** - Explain merge strategy and approval rationale
9. **Maintain quality** - Consistently enforce quality standards
10. **Communicate clearly** - Use structured comments with clear action items

## Tips for Efficiency

- Use the triage dashboard script regularly (`./tools/triage-prs.ps1`)
- Set up GitHub CLI aliases for common commands
- Create templates for common review comments
- Batch similar actions (e.g., merge all ready PRs at once)
- Use labels to track PR status (if helpful)
- Set up notifications for CI failures
- Review smaller PRs first (quicker wins)
- Create follow-up issues liberally (don't block on minor issues)

## Escalation

When to escalate to project maintainer:
- Multiple agents stalled despite restart attempts
- Systemic CI issues you can't fix
- Quality concerns about project direction
- Security concerns
- Need for architectural decisions
- Conflict between agents or PRs

## See Also

- [PR Review Playbook](pr-review.md) - Human review guidelines
- [Autonomy Modes](autonomy-modes.md) - Agent workflow control
- [Agent Assignment](../docs/agent-assignment.md) - Role label usage
- [GitHub Labels](../docs/github-labels.md) - Label definitions
- [Quality Bar](../specs/kerrigan/030-quality-bar.md) - Quality standards
