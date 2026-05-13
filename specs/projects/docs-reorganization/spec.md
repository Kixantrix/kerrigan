# Spec: Documentation Reorganization

## Overview

Reorganize Kerrigan's documentation structure to improve navigability for both agents and humans. Move from a flat 20-file `docs/` directory to a hierarchical structure with clear ownership.

## Goals

1. **Improve discoverability**: Agents know where to find/update specific doc types
2. **Separate current from historical**: Archive completed milestones and research artifacts
3. **Clarify ownership**: Distinguish setup guides, operational runbooks, and architecture docs
4. **Reduce confusion**: Make `specs/projects/` and `prompts/` vs `.github/agents/` distinctions clear

## Success Criteria

- [ ] `docs/` has 4 subdirectories: `onboarding/`, `architecture/`, `operations/`, `_archive/`
- [ ] AGENTS.md updated to remove "v1 phasing out" language (state v2 as current)
- [ ] `specs/projects/README.md` exists with status legend for all 11 projects
- [ ] `prompts/README.md` and `.github/agents/README.md` clarify the distinction
- [ ] Setup guides moved from `playbooks/` to `docs/operations/`
- [ ] All internal links updated to reflect new paths
- [ ] Hygiene validator passes (no broken links)

## Out of Scope

- Content rewrites (only moves and minor clarifications)
- Deleting files (archive instead for audit trail)
- Changing spec-kit artifacts (`.specify/` untouched)

## Constraints

- Preserve git history for moved files (use `git mv`)
- Update all internal links to prevent breakage
- Run hygiene validator after changes

## Reference

- [Audit results](../../../feedback/design-feedback/) (from Explore subagent)
- [AGENTS.md](../../../AGENTS.md) - needs v1 reference cleanup
- [Current docs structure](../../../docs/) - 20 files, flat
- [specs/projects](../) - 11 projects, unclear status
