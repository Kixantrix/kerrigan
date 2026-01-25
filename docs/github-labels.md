# GitHub Labels for Kerrigan

This document lists all required GitHub labels for Kerrigan's agent workflow and autonomy controls.

## Required Labels

### Autonomy Control Labels

These labels control when agents are allowed to work on issues and PRs:

- **`agent:go`** (color: `#0E8A16`, green)
  - Grants agents permission to work on this issue/PR
  - Required for on-demand mode (default)
  - See: `playbooks/autonomy-modes.md`

- **`agent:sprint`** (color: `#FBCA04`, yellow)
  - Marks an issue as a sprint tracking issue
  - PRs linked to sprint issues automatically get `agent:go`
  - Used for sprint mode autonomy
  - See: `playbooks/autonomy-modes.md`

- **`autonomy:override`** (color: `#D93F0B`, red)
  - Human-only label to bypass autonomy gates
  - Use when you need to merge without agent approval
  - See: `playbooks/autonomy-modes.md`

### Quality Control Labels

- **`allow:large-file`** (color: `#C5DEF5`, light blue)
  - Bypasses the 800 LOC quality bar check
  - Use sparingly, only when justified
  - See: `specs/kerrigan/030-quality-bar.md`

### Testing Status Labels

- **`needs:manual-testing`** (color: `#EDEDED`, light gray)
  - PR requires human verification before merge
  - Applied when functionality cannot be fully automated tested
  - See: `playbooks/manual-testing.md`

- **`tested:manual`** (color: `#0E8A16`, green)
  - Human confirmed manual testing complete
  - Applied after manual testing documented in PR
  - See: `playbooks/manual-testing.md`

### Tier Labels (Autonomy Level)

These labels define the level of autonomy and gating for issues:

- **`tier:auto`** (color: `#28A745`, bright green)
  - Fully autonomous - no manual gates required
  - Issues automatically get `agent:go` when created
  - Work proceeds without human intervention until completion
  - Use for: low-risk tasks, routine maintenance, documentation

- **`tier:standard`** (color: `#FFA500`, orange)
  - Standard workflow - acceptance gate only
  - Human reviews and approves final PR before merge
  - Agent works autonomously but waits for approval
  - Default for most issues (if no tier specified)

- **`tier:strategic`** (color: `#DC143C`, crimson)
  - High-touch - direction and acceptance gates
  - Human provides strategic direction during work
  - Agent pauses for directional input when needed
  - Human reviews and approves before merge
  - Use for: complex features, architectural changes, risky operations

- **`blocked`** (color: `#E99695`, soft coral)
  - Issue is blocked and cannot proceed
  - Removed automatically when dependencies resolve
  - Manual label for issues with external blockers

### Role Assignment Labels

These labels are used for assigning work to specific agent roles:

- **`role:spec`** (color: `#5319E7`, purple)
  - Assigns issue to Spec agent
  - Produces: spec.md, acceptance-tests.md
  - See: `.github/agents/role.spec.md`

- **`role:architect`** (color: `#1D76DB`, blue)
  - Assigns issue to Architect agent
  - Produces: architecture.md, plan.md, tasks.md, test-plan.md
  - See: `.github/agents/role.architect.md`

- **`role:swe`** (color: `#006B75`, teal)
  - Assigns issue to Software Engineering agent
  - Implements features following the plan
  - See: `.github/agents/role.swe.md`

- **`role:testing`** (color: `#7057FF`, violet)
  - Assigns issue to Testing agent
  - Adds test coverage and validation
  - See: `.github/agents/role.testing.md`

- **`role:debugging`** (color: `#D93F0B`, orange-red)
  - Assigns issue to Debugging agent
  - Investigates and fixes issues
  - See: `.github/agents/role.debugging.md`

- **`role:security`** (color: `#B60205`, dark red)
  - Assigns issue to Security agent
  - Reviews security and adds safeguards
  - See: `.github/agents/role.security.md`

- **`role:deployment`** (color: `#0E8A16`, green)
  - Assigns issue to Deployment agent
  - Creates deployment artifacts and runbooks
  - See: `.github/agents/role.deployment.md`

- **`role:triage`** (color: `#FBCA04`, yellow)
  - Assigns issue to Triage agent
  - Reviews PRs, manages CI issues, approves and merges
  - See: `.github/agents/role.triage.md`

- **`role:design`** (color: `#E99695`, soft pink/coral)
  - Assigns issue to Design agent
  - Creates design systems, components, and visual specifications
  - See: `.github/agents/role.design.md` (to be created)

### Project Labels (optional but recommended)

- **`kerrigan`** (color: `#000000`, black)
  - Tags issues related to Kerrigan system itself
  - Useful for filtering meta-work from project work

## Creating Labels via GitHub CLI

If you have GitHub CLI installed, you can create all required labels with:

```bash
# Autonomy control labels
gh label create "agent:go" --color "0E8A16" --description "Grants agents permission to work on this issue/PR" || echo "Label agent:go already exists"
gh label create "agent:sprint" --color "FBCA04" --description "Sprint tracking issue - PRs auto-get agent:go" || echo "Label agent:sprint already exists"
gh label create "autonomy:override" --color "D93F0B" --description "Human override to bypass autonomy gates" || echo "Label autonomy:override already exists"

# Quality control
gh label create "allow:large-file" --color "C5DEF5" --description "Bypass 800 LOC quality bar check" || echo "Label allow:large-file already exists"

# Testing status
gh label create "needs:manual-testing" --color "EDEDED" --description "PR requires human verification" || echo "Label needs:manual-testing already exists"
gh label create "tested:manual" --color "0E8A16" --description "Manual testing complete" || echo "Label tested:manual already exists"

# Tier labels (autonomy level)
gh label create "tier:auto" --color "28A745" --description "Fully autonomous - no manual gates" || echo "Label tier:auto already exists"
gh label create "tier:standard" --color "FFA500" --description "Standard workflow - acceptance gate only" || echo "Label tier:standard already exists"
gh label create "tier:strategic" --color "DC143C" --description "High-touch - direction and acceptance gates" || echo "Label tier:strategic already exists"
gh label create "blocked" --color "E99695" --description "Issue is blocked and cannot proceed" || echo "Label blocked already exists"

# Role assignment
gh label create "role:spec" --color "5319E7" --description "Assign to Spec agent" || echo "Label role:spec already exists"
gh label create "role:architect" --color "1D76DB" --description "Assign to Architect agent" || echo "Label role:architect already exists"
gh label create "role:swe" --color "006B75" --description "Assign to SWE agent" || echo "Label role:swe already exists"
gh label create "role:testing" --color "7057FF" --description "Assign to Testing agent" || echo "Label role:testing already exists"
gh label create "role:debugging" --color "D93F0B" --description "Assign to Debugging agent" || echo "Label role:debugging already exists"
gh label create "role:security" --color "B60205" --description "Assign to Security agent" || echo "Label role:security already exists"
gh label create "role:deployment" --color "0E8A16" --description "Assign to Deployment agent" || echo "Label role:deployment already exists"
gh label create "role:triage" --color "FBCA04" --description "Assign to Triage agent" || echo "Label role:triage already exists"
gh label create "role:design" --color "E99695" --description "Assign to Design agent" || echo "Label role:design already exists"

# Optional project label
gh label create "kerrigan" --color "000000" --description "Kerrigan system meta-work" || echo "Label kerrigan already exists"
```

**Note**: The `|| echo` fallback ensures the script continues even if labels already exist.

## Creating Labels via GitHub Web UI

1. Navigate to your repository on GitHub
2. Click on "Issues" tab
3. Click on "Labels" button
4. Click "New label" button
5. Enter the label name, color, and description from the lists above
6. Click "Create label"
7. Repeat for all required labels

## Verification

After creating labels, verify they exist:

```bash
gh label list
```

Or check via the GitHub web UI at: `https://github.com/OWNER/REPO/labels`

## See Also

- [Autonomy Modes](../playbooks/autonomy-modes.md) - How autonomy labels control agent workflow
- [Agent Assignment](agent-assignment.md) - How to use role labels
- [Setup Guide](setup.md) - Complete setup instructions including labels
