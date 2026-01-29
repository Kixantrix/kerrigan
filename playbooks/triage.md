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

### 5. Handle Manual Testing Requirements

Some PRs require manual verification that cannot be automated. Look for the `needs:manual-testing` label or "Manual Testing Required" section in the PR description.

#### Step 1: Identify Manual Testing Requirements

Check the PR's Testing Classification section:
```bash
gh pr view <PR#>
```

Look for:
- "Manual Testing Required" section with specific test cases
- `needs:manual-testing` label

#### Step 2: Verify Testing Instructions Are Clear

Manual testing requirements should include:
- Clear description of what to test
- How to trigger the test scenario
- Expected outcome
- How to verify success

If instructions are unclear:
```bash
gh pr comment <PR#> --body "Please clarify manual testing requirements:
- What specific behavior should I test?
- How do I trigger this scenario?
- What is the expected outcome?

See playbooks/manual-testing.md for guidance."
```

#### Step 3: Perform Manual Testing

Follow the testing instructions provided in the PR. Common scenarios:

**For GitHub Actions workflows:**
```bash
# View workflow runs
gh run list --workflow=workflow-name.yml

# Trigger workflow manually (if supported)
gh workflow run workflow-name.yml

# Monitor execution
gh run watch

# View logs
gh run view <RUN_ID> --log
```

**For UI changes:**
- Check screenshots provided in PR
- Test locally if changes are significant
- Verify responsive behavior if applicable

**For API integrations:**
- Review test environment setup
- Verify test results documented in PR
- Check for proper error handling

#### Step 4: Document Test Results

After completing manual testing, add a comment documenting results:
```bash
gh pr comment <PR#> --body "## Manual Testing Results

✅ **[Test scenario name]** - Tested successfully
- [Specific steps taken]
- [Results observed]
- [Link to workflow run/screenshot if applicable]

Manual testing complete. Adding `tested:manual` label."
```

Then update labels:
```bash
# Add tested:manual label
gh pr edit <PR#> --add-label "tested:manual"

# Remove needs:manual-testing label
gh pr edit <PR#> --remove-label "needs:manual-testing"
```

#### Step 5: Proceed with Review

Once manual testing is complete and documented:
- Continue with normal PR review process
- Approve if all other checks pass
- Merge when ready

**Important:** Do not merge PRs with `needs:manual-testing` label unless:
- Manual testing completed and documented, OR
- Cannot-test justification is acceptable with mitigation plan

See `playbooks/manual-testing.md` for complete manual testing guidelines.

### 6. Handle Merge Conflicts

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

# CRITICAL: Always set GIT_EDITOR='true' to prevent entering interactive editor mode
# This avoids agent stalls caused by nano/vi waiting for input
GIT_EDITOR='true' git rebase --continue

# Force push
git push --force-with-lease
```

**Important Note:** Always use `GIT_EDITOR='true'` before `git rebase --continue` to prevent the agent from entering interactive editor mode (nano/vi), which causes complete workflow stalls. The `true` command exits immediately, allowing git to use default commit messages.

### 7. Restart Stalled Agents

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

# If there are conflicts, resolve them and continue:
git add .
# CRITICAL: Always use GIT_EDITOR='true' to prevent interactive editor stalls
GIT_EDITOR='true' git rebase --continue

git push --force-with-lease

# Comment again
gh pr comment <PR#> --body "@copilot Please continue. I've rebased this PR on main."
```

### 8. Create Follow-up Issues

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
- [ ] Manual testing documented if required (see `playbooks/manual-testing.md`)
- [ ] `needs:manual-testing` label applied if manual testing required
- [ ] `tested:manual` label added if manual testing completed

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

## Wave-Based Issue Assignment Strategy

### Overview

Wave-based assignment minimizes merge conflicts when multiple Copilot agents work in parallel by grouping issues based on file overlap and assigning them sequentially.

### The Problem

When agents work on multiple issues simultaneously:
- **Parallel branches** often conflict with each other
- **Rebase overhead** - Triage must manually resolve conflicts
- **Wasted work** - Changes sometimes get overwritten or duplicated
- **CI retriggers** - Each rebase requires close/reopen to trigger CI
- **Stale context** - Agents work against outdated main branch

### The Solution

**Wave-based assignment** groups issues by predicted file overlap and assigns one wave at a time:

1. **Wave 1**: Independent issues (no file overlap with other issues)
2. **Wave 2**: Issues that may overlap with Wave 1
3. **Wave 3**: Issues dependent on earlier waves
4. **Wave 4+**: Additional dependent issues

### Wave Assignment Process

#### Step 1: Analyze Open Issues

Review all open issues that are ready for assignment (`agent:go` or sprint issues):

```bash
# View all open issues
./tools/show-issues.ps1

# Or use GitHub CLI
gh issue list --state open --label "agent:go"
```

#### Step 2: Predict File Overlap

Analyze each issue to predict which files will be modified:

**Sources for prediction:**
- **Specs/tasks**: Look at "Files to Modify" sections in linked specs
- **Issue description**: Mentions of specific files, directories, or components
- **Historical data**: Similar issues in the past touched which files?
- **Common patterns**:
  - Workflow changes → `.github/workflows/`, `.github/test-mapping.yml`
  - Documentation → `docs/`, `playbooks/`, `README.md`
  - Core infrastructure → `tools/`, `scripts/`
  - Tests → `tests/`, test files in relevant areas

**Example analysis:**
- Issue #159: "Update CI workflow" → likely touches `.github/workflows/ci.yml`
- Issue #160: "Add validation script" → likely touches `tools/validators/`
- Issue #161: "Update workflow permissions" → likely touches `.github/workflows/ci.yml`

In this case, #159 and #161 have file overlap (both touch ci.yml), so they should be in different waves.

#### Step 3: Group Issues into Waves

**Wave 1 criteria** (assign first):
- No predicted file overlap with any other open issue
- Independent changes that won't conflict
- Quick wins that can merge fast
- Documentation-only changes (usually safe)

**Wave 2+ criteria** (assign after previous wave merges):
- Predicted file overlap with Wave 1 issues
- Dependent on Wave 1 changes
- Touch high-conflict areas (workflows, shared configs)

**Grouping guidelines:**
- Keep wave size manageable (3-7 issues per wave)
- Prioritize high-value issues in earlier waves
- Group related issues together when they don't conflict
- Consider issue complexity (mix quick and complex issues)

#### Step 4: Apply Wave Labels

Label issues with their wave assignment:

```bash
# Wave 1 (independent issues)
gh issue edit 159 --add-label "wave:1"
gh issue edit 162 --add-label "wave:1"
gh issue edit 165 --add-label "wave:1"

# Wave 2 (overlap with Wave 1 or dependent)
gh issue edit 160 --add-label "wave:2"
gh issue edit 161 --add-label "wave:2"
gh issue edit 163 --add-label "wave:2"

# Wave 3 (dependent on Wave 2)
gh issue edit 164 --add-label "wave:3"
```

Or use PowerShell for batch assignment:

```powershell
# Wave 1
$wave1 = 159,162,165
foreach ($issue in $wave1) {
    gh issue edit $issue --add-label "wave:1"
}

# Wave 2
$wave2 = 160,161,163
foreach ($issue in $wave2) {
    gh issue edit $issue --add-label "wave:2"
}
```

#### Step 5: Assign Wave 1 to Agents

Only assign Wave 1 issues initially:

```bash
# Assign Wave 1 issues to @copilot
gh issue edit 159 --add-assignee "@copilot"
gh issue edit 162 --add-assignee "@copilot"
gh issue edit 165 --add-assignee "@copilot"
```

Or in bulk:

```powershell
$wave1 = 159,162,165
foreach ($issue in $wave1) {
    gh issue edit $issue --add-assignee "@copilot"
}
```

**Important**: Do NOT assign Wave 2+ issues yet. They will be assigned after Wave 1 merges.

#### Step 6: Monitor Wave 1 Progress

Track Wave 1 PRs through to merge:

```powershell
# Check PR status
./tools/triage-prs.ps1

# View Wave 1 issues
gh issue list --label "wave:1"
```

Review, approve, and merge Wave 1 PRs as they complete. Follow standard triage workflows.

#### Step 7: Assign Next Wave

**Only after all Wave 1 PRs are merged**, assign Wave 2:

```bash
# Check Wave 1 status (should all be closed)
gh issue list --label "wave:1" --state open

# If all closed, assign Wave 2
gh issue edit 160 --add-assignee "@copilot"
gh issue edit 161 --add-assignee "@copilot"
gh issue edit 163 --add-assignee "@copilot"
```

Repeat this process for each subsequent wave.

### Wave Assignment Decision Tree

```
Open Issues Ready for Assignment
  │
  ├─ Analyze file overlap
  │   └─ Predict which files each issue will modify
  │
  ├─ Group into waves
  │   ├─ Wave 1: No overlap, independent
  │   ├─ Wave 2: Overlaps with Wave 1
  │   └─ Wave 3+: Dependent on earlier waves
  │
  ├─ Label issues with wave:N
  │
  ├─ Assign Wave 1 only
  │   └─ Add assignee @copilot
  │
  ├─ Monitor Wave 1
  │   ├─ Review PRs
  │   ├─ Approve quality work
  │   └─ Merge when ready
  │
  ├─ Wave 1 complete? (all PRs merged)
  │   ├─ Yes → Assign Wave 2
  │   └─ No → Continue monitoring
  │
  └─ Repeat for each wave
```

### File Overlap Detection Strategies

#### Strategy 1: Explicit Spec Analysis (Most Reliable)

Check linked spec documents for "Files to Modify" or similar sections:

```bash
# View issue and linked specs
gh issue view <NUMBER>

# Check project folder
ls specs/projects/<project-name>/
cat specs/projects/<project-name>/tasks.md
```

Look for explicit file listings in specs.

#### Strategy 2: Issue Description Keywords

Scan issue descriptions for file/directory mentions:
- Direct file paths: `.github/workflows/ci.yml`
- Directory mentions: "in the `tools/validators/` directory"
- Component names: "update the triage script" → `tools/triage-prs.ps1`

#### Strategy 3: Historical Pattern Matching

Use past issues as reference:
- Similar issue type → likely similar files
- Same role label → often touches same areas
- Workflow changes → almost always touch `.github/workflows/`

**Common patterns:**
- `role:triage` → `playbooks/triage.md`, `.github/agents/role.triage.md`
- `role:swe` + "CI" → `.github/workflows/`, `.github/test-mapping.yml`
- "documentation" → `docs/`, `playbooks/`, `README.md`
- "validator" → `tools/validators/`
- "label" → `docs/github-labels.md`

#### Strategy 4: Conservative Grouping

When in doubt:
- Put potential overlaps in different waves
- Err on the side of more waves (safer)
- Group only when confident no overlap exists

### Trade-offs and Considerations

| Factor | Serial | Wave-based | Parallel |
|--------|--------|------------|----------|
| Conflicts | None | Minimal | Many |
| Throughput | Low | Medium | High (theoretical) |
| Triage overhead | Low | Low-Medium | High |
| Forward progress | Slow | Good | Fast (when no conflicts) |
| Complexity | Simple | Moderate | Simple but messy |

**When to use wave-based:**
- Multiple issues ready for assignment
- Issues touch common areas (workflows, configs, docs)
- Previous parallel work caused conflicts
- Want predictable progress without rebase overhead

**When to use parallel (skip waves):**
- Issues touch completely different subsystems
- All issues are documentation-only
- Very small changes unlikely to conflict
- Time pressure and willing to risk conflicts

**When to use serial (one at a time):**
- High-risk changes (major refactors, breaking changes)
- Complex dependencies between issues
- Learning period (understanding what conflicts arise)

### Best Practices

1. **Start conservative** - Use smaller waves initially, expand as you learn patterns
2. **Document predictions** - Note why you grouped issues in specific waves (helps future learning)
3. **Monitor actual conflicts** - Track which issues actually conflicted to improve predictions
4. **Balance wave size** - 3-7 issues per wave is usually optimal
5. **Prioritize within waves** - High-value issues earlier
6. **Update assignments proactively** - Assign next wave as soon as previous merges
7. **Communicate wave status** - Let stakeholders know which wave is active
8. **Use labels consistently** - Always label waves even if assignment is immediate

### Common Scenarios

#### Scenario 1: Wave 1 Has Stalled PR

**Problem**: One Wave 1 PR is stalled, others have merged

**Solution**:
- Don't block Wave 2 on one stalled PR
- If stalled PR has no overlap with Wave 2, proceed with Wave 2
- If overlap exists, either:
  - Wait and restart the stalled agent, OR
  - Close stalled PR, create follow-up issue, assign to later wave

#### Scenario 2: Urgent Issue Needs Immediate Assignment

**Problem**: Critical issue arises mid-wave

**Solution**:
- Assess file overlap with current wave
- If no overlap: Assign immediately (don't wait for wave)
- If overlap: Either:
  - Rush-merge blocking PRs in current wave, OR
  - Assign to human for immediate fix

#### Scenario 3: Wave 1 PR Conflicts with Wave 2 PR

**Problem**: Despite predictions, Wave 1 and Wave 2 PRs conflict

**Solution**:
- This shouldn't happen if waves assigned correctly
- Review: Was file prediction wrong?
- Learn: Update prediction strategy
- Fix: Rebase Wave 2 PR after Wave 1 merges

#### Scenario 4: Too Many Issues for Wave System

**Problem**: 20+ issues ready for assignment

**Solution**:
- Group into 3-5 waves
- Assign Wave 1-2 immediately (if no overlap between them)
- Queue remaining waves
- Consider parallel execution of non-overlapping waves

### Wave Management Script (Optional)

For automated wave management, consider creating `tools/manage-waves.ps1`:

```powershell
# Pseudocode for wave management script
# Check Wave N status
$waveN_issues = gh issue list --label "wave:$N" --state open --json number

# If wave empty, assign next wave
if ($waveN_issues.Count -eq 0) {
    $nextWave = $N + 1
    $nextWaveIssues = gh issue list --label "wave:$nextWave" --state open --json number
    foreach ($issue in $nextWaveIssues) {
        gh issue edit $issue.number --add-assignee "@copilot"
    }
}
```

### Metrics to Track

**Wave effectiveness:**
- Conflicts per wave (goal: 0-1 per wave)
- Time to complete wave (goal: track and optimize)
- Wave size vs completion time (find optimal size)
- Prediction accuracy (predicted overlap vs actual conflicts)

**Process metrics:**
- Issues assigned per week (with vs without waves)
- PRs merged per week (with vs without waves)
- Average time to merge (with vs without waves)
- Rebase overhead (conflicts resolved manually)

## See Also

- [PR Review Playbook](pr-review.md) - Human review guidelines
- [Autonomy Modes](autonomy-modes.md) - Agent workflow control
- [Agent Assignment](../docs/agent-assignment.md) - Role label usage
- [GitHub Labels](../docs/github-labels.md) - Label definitions
- [Quality Bar](../specs/kerrigan/030-quality-bar.md) - Quality standards
- [Git Best Practices](../docs/git-best-practices.md) - Preventing interactive editor stalls and git operation guidelines
