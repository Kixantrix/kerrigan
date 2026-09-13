# GitHub Labels for Kerrigan

Kerrigan v2 uses **4 labels** as annotations for the optional issue adapter. Direct app sessions do not require labels or issues; follow [session operations](../../playbooks/session-operations.md) for accepted authority, explicit executor dispatch, and accountable runtime stopping. Labels do not enforce runtime control or select a profile.

## Issue-adapter annotations

| Label | Color | Purpose |
|-------|-------|---------|
| `agent:go` | `#0E8A16` (green) | Issue ready for explicit assignment |
| `agent:wait` | `#FBCA04` (yellow) | Issue intentionally waiting; not a runtime stop |
| `agent:local` | `#5319E7` (purple) | Requires human's machine (device I/O, secrets) |
| `autonomy:override` | `#D93F0B` (red) | Human-approved exception where a configured gate supports it |

Issue creation/readiness is not assignment, and assignment metadata is not worker-start evidence. The coordinator verifies explicit assignment and ownership acknowledgment. To pause active work, use its owner's supported runtime stop and confirm process/resource release. Honor actual repository-specific merge gates; this repository does not implement an autonomy-label gate.

### Optional Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `allow:large-file` | `#C5DEF5` (light blue) | Bypass the 800 LOC quality bar check |
| `needs:manual-testing` | `#EDEDED` (light gray) | PR requires human verification |
| `tested:manual` | `#0E8A16` (green) | Manual testing confirmed complete |

## Creating Labels via GitHub CLI

```bash
# Optional issue adapter (4 annotations)
gh label create "agent:go" --color "0E8A16" --description "Issue ready for explicit assignment" --force
gh label create "agent:wait" --color "FBCA04" --description "Issue intentionally waiting; not a runtime stop" --force
gh label create "agent:local" --color "5319E7" --description "Requires human machine" --force
gh label create "autonomy:override" --color "D93F0B" --description "Human override for blocked gate" --force

# Optional
gh label create "allow:large-file" --color "C5DEF5" --description "Bypass 800 LOC quality bar" --force
gh label create "needs:manual-testing" --color "EDEDED" --description "PR requires human verification" --force
gh label create "tested:manual" --color "0E8A16" --description "Manual testing complete" --force
```

## Verification

```bash
gh label list
```

## See Also

- [Autonomy Modes](autonomy-modes.md) - Session authority and optional issue-adapter annotations
- [Setup Guide](../onboarding/setup.md) - Complete setup instructions
- [AGENTS.md](../../AGENTS.md) - Label usage in agent profiles
