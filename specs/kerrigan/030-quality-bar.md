# Quality bar (applies from first PR)

## Definition of done
A change is "done" when:
- It satisfies acceptance criteria (or advances toward them in a milestone)
- Automated tests exist for behavior or appropriate scaffolding exists
- CI is green
- Documentation is updated (spec/plan/runbook as applicable)
- The change is reviewable (small and focused)

## Structural heuristics (enforced by CI where possible)

### No giant blob files by default
- Large single files reduce agent and human comprehension.
- Default thresholds:
  - **Warn** if any single source file exceeds 400 LOC
  - **Fail** if any single source file exceeds 800 LOC
- Exceptions:
  - generated files (ignored)
  - a PR label `allow:large-file` (human override)

### Keep entrypoints short
- README and playbooks should guide agents within ~100 lines.
- Use links, not walls of text.

### Tests are not optional
- Features: tests required.
- Bug fixes: regression test required.
- Infrastructure-first: ensure a test harness exists early in the project lifecycle.

### Security basics
- Never commit secrets.
- Prefer least privilege and explicit environments.
- Runbook must include secret management notes if deployable.

## Review checklist (PR template)
- [ ] Links to relevant spec/plan/tasks
- [ ] Tests added/updated
- [ ] CI green
- [ ] Docs updated
- [ ] No unnecessary large files or monoliths
