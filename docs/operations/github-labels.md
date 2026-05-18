# GitHub Labels for Kerrigan

Kerrigan v2 uses **4 labels** for autonomy control. That's it.

## Required Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `agent:go` | `#0E8A16` (green) | Agent has autonomy — proceed |
| `agent:wait` | `#FBCA04` (yellow) | Blocked on human — stop |
| `agent:local` | `#5319E7` (purple) | Requires human's machine (device I/O, secrets) |
| `autonomy:override` | `#D93F0B` (red) | Human override for a blocked gate |

### Optional Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `allow:large-file` | `#C5DEF5` (light blue) | Bypass the 800 LOC quality bar check |
| `needs:manual-testing` | `#EDEDED` (light gray) | PR requires human verification |
| `tested:manual` | `#0E8A16` (green) | Manual testing confirmed complete |

## Creating Labels via GitHub CLI

```bash
# Required (4 labels)
gh label create "agent:go" --color "0E8A16" --description "Agent has autonomy - proceed" --force
gh label create "agent:wait" --color "FBCA04" --description "Blocked on human - stop" --force
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

- [Autonomy Modes](autonomy-modes.md) - How labels control agent workflow
- [Setup Guide](../onboarding/setup.md) - Complete setup instructions
- [AGENTS.md](../../AGENTS.md) - Label usage in agent profiles
