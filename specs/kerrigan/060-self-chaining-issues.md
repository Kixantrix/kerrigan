# Issue Template for Self-Chaining Agent Work

When creating agent-driven issues, include this section to enable automatic progression:

## On Completion

When this issue is complete and merged, **the agent should create the next issue** with:

**Title**: `"[Next milestone/task title]"`  
**Labels**: `agent:go, [relevant-role-labels], kerrigan`  
**Body Template**:
```
[Clear goal statement]

## Goal
[What this milestone achieves]

## Scope
- [Specific deliverables]
- [Boundaries/non-goals]

## Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] CI passes
- [ ] Tests added/updated

## References
- [Link to plan.md section]
- [Link to tasks.md section]
- [Link to relevant specs]

## On Completion
[Instructions for creating the NEXT issue, creating a chain]

---
**Current Status**: [Previous milestone] complete, starting [This milestone]
**Deliverable**: [Key output]
```

## Agent Instructions for Issue Creation

When completing an issue that has an "On Completion" section:

1. **Before closing the PR**: Create the next issue using `gh issue create`
2. **Reference the chain**: Mention "Continues from #X" in the new issue
3. **Maintain momentum**: Add `agent:go` label immediately if no human review needed
4. **Update plan.md**: Mark current milestone progress
5. **Comment on completed issue**: Link to the new issue you created

This creates a self-sustaining agent workflow where completing one task automatically queues the next.

## Example Command

```bash
gh issue create \
  --title "Milestone 4: Add test coverage for validators" \
  --label "agent:go,testing,kerrigan" \
  --body "Continues from #3. Add unit tests for check_artifacts.py and check_quality_bar.py per test-plan.md..."
```

## Benefits

- **Continuous progress**: No waiting between milestones
- **Clear lineage**: Each issue references previous work
- **Autonomy control**: Human can remove `agent:go` to pause the chain
- **Traceable history**: GitHub issues show the full progression
