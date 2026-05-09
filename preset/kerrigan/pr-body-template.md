## Summary

<!-- One sentence: what this PR does and why. -->
[Brief description of the change]

Closes #[ISSUE]

---

## Acceptance Criteria

<!-- Mirror the ACs from the issue. Check each one that this PR fully satisfies. -->

- [ ] AC-1: [Copy AC text from issue]
- [ ] AC-2: [Copy AC text from issue]
- [ ] AC-3: [Copy AC text from issue]

---

## Routing

<!-- State the routing rule applied to this task (from plan.md Delegation section). -->

**Rule applied**: `R-cloud-default` | `R-local-required` | `R-hybrid` *(pick one)*  
**Rationale**: [One sentence, e.g. "No device-io.* or paid-service.* capabilities required."]

---

## Changes

<!-- List the files created or modified. Keep it to the meaningful ones. -->

| File | Change |
|---|---|
| `[path/to/file]` | Created / Modified / Deleted |
| `[path/to/file]` | Created / Modified / Deleted |

---

## Test Commands

<!-- Commands a reviewer can run to verify this PR locally. Stack-agnostic placeholders — replace with real commands. -->

```sh
# Run the project's test suite
[test command, e.g. pytest / cargo test / npm test / go test ./...]

# Run just the tests relevant to this change
[focused test command]

# Smoke check (if scripts/smoke.sh exists)
scripts/smoke.sh
```

---

## Verification Checklist

- [ ] CI is green
- [ ] All ACs above are checked
- [ ] `touch` globs in tasks.md match the files actually changed
- [ ] No secrets committed
- [ ] Docs updated if behaviour changed
- [ ] Spec/plan/tasks links at the top of this PR are accurate
