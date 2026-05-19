# Agent Frontmatter Upgrade - Acceptance Tests

## Milestone 1: Update Agent Frontmatter

### Test 1.1: All Agent Files Have Valid Frontmatter
- [ ] All `.md` files in `.github/agents/` have YAML frontmatter
- [ ] Each frontmatter includes `name` and `description` fields
- [ ] Frontmatter is valid YAML (parseable)

### Test 1.2: Agents Appear in GitHub UI
- [ ] Navigate to repository's agent sessions
- [ ] Verify all custom agents appear in the agent dropdown
- [ ] Confirm agents can be selected and invoked directly

### Test 1.3: Agent Functionality Preserved
- [ ] Each agent responds appropriately when invoked
- [ ] Existing issue-based workflow continues to work
- [ ] No regressions in agent behavior

## Milestone 2: Assignment Strategy Investigation

### Test 2.1: Comparison Document Created
- [ ] Document comparing issue-based vs direct agent session approaches
- [ ] Trade-offs matrix with pros/cons
- [ ] Recommendation for optimal workflow

## Manual Verification Steps

1. After frontmatter update, create a new agent session in GitHub
2. Verify each agent appears in dropdown
3. Test invoking each agent directly
4. Document any issues encountered
