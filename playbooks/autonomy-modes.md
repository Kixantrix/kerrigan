# Autonomy modes

Goal: allow agents to open PRs directly when helpful, while retaining an easy "pause / on-demand" switch.

## Automation Features

**New in v2**: Kerrigan now includes automation workflows to reduce manual intervention:
- **Auto-assign reviewers**: Based on role labels (role:swe, role:testing, etc.)
- **Auto-assign issues**: Issues with role labels auto-assign to configured users
- **Auto-generate issues**: Create issues from tasks.md with `<!-- AUTO-ISSUE -->` markers
- **Sprint mode auto-approval**: PRs linked to `agent:sprint` issues auto-receive `agent:go` label

See `.github/automation/README.md` for setup instructions.

## Mode A — On-demand (recommended default)
- Agents may only open PRs when the linked issue is labeled `agent:go`.
- If not labeled, CI fails with an autonomy gate message.

## Mode B — Autonomous sprint
- Label a single tracking issue/milestone as `agent:sprint`.
- Agents may open PRs referencing that tracking issue until the milestone is met.
- After the milestone PR merges, agents should stop.
- **Automation**: PRs linked to sprint issues automatically receive `agent:go` label.

## Mode C — Hybrid
- Spec + Architecture roles may propose PRs anytime.
- SWE/Testing/Deployment require `agent:go`.

## Overrides
- Add PR label `autonomy:override` (human-only) to bypass the gate.
- Add PR label `allow:large-file` to bypass large-file checks (use sparingly).

## Implementation details

The autonomy gate is enforced by `.github/workflows/agent-gates.yml`, which:

1. **Runs on PR events**: opened, synchronize, reopened, labeled, unlabeled
2. **Checks for override first**: If PR has `autonomy:override` label, gate passes immediately
3. **Extracts linked issues**: Parses PR body for issue references (e.g., "Fixes #123", "Closes #456")
4. **Checks issue labels**: Uses GitHub API to fetch labels on linked issues
5. **Validates autonomy grant**:
   - **On-demand mode**: Requires `agent:go` label on at least one linked issue
   - **Sprint mode**: Requires `agent:sprint` label on at least one linked issue
   - **Fallback**: If no linked issues, checks PR labels directly for `agent:go` or `agent:sprint`
6. **Fails with clear message**: If no autonomy grant found, provides actionable steps to proceed

### Example patterns recognized

The workflow recognizes these patterns in PR body:
- `Fixes #123`, `Closes #456`, `Resolves #789`
- `Issue #123`, `Ref #456`, `See #789`
- `#123` (standalone, with whitespace around it)

### Testing the gate

**Test Scenario 1: PR without required labels**
- Create PR without linking to any issue
- Expected: Gate fails with message about missing labels
- Fix: Add `agent:go` label to PR or link to an issue with `agent:go`

**Test Scenario 2: PR with linked issue (on-demand mode)**
- Create issue with `agent:go` label
- Create PR with "Fixes #N" in body
- Expected: Gate passes

**Test Scenario 3: Sprint mode**
- Create issue with `agent:sprint` label
- Create PR referencing that issue
- Expected: Gate passes

**Test Scenario 4: Override**
- Create PR without any linked issues
- Add `autonomy:override` label to PR
- Expected: Gate passes immediately

**Test Scenario 5: Large file bypass**
- Create PR with `allow:large-file` label
- Expected: Gate logs the label but doesn't affect autonomy check (used by quality bar validator)

### Limitations and workarounds

- **Manual approval fallback**: If GitHub API is unavailable, gates may not enforce properly. Use manual PR review as fallback.
- **Label propagation delay**: GitHub Actions may take a few seconds to trigger after label changes. Wait and check workflow status.
- **Issue linking required**: For best results, always link PRs to issues using recognized patterns in PR body.
- **Mode C (Hybrid) not automated**: Mode C requires custom logic. Use Mode A or B for automated enforcement.
