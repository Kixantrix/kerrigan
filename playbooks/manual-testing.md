# Manual Testing Playbook

This playbook provides guidance on identifying, documenting, and performing manual testing for functionality that cannot be adequately covered by automated tests.

## Overview

Some functionality requires human verification or real-world conditions that cannot be replicated in automated tests. This playbook helps identify such scenarios, communicate testing requirements, and document test results.

## When Manual Testing is Required

Manual testing is necessary when functionality:

1. **Requires real external systems**: GitHub webhooks, OAuth providers, third-party APIs
2. **Involves visual verification**: UI/UX changes, responsive design, accessibility
3. **Depends on real-world timing**: Performance characteristics, rate limiting, timeouts
4. **Needs human judgment**: User experience flows, error message clarity
5. **Cannot be automated safely**: Deployment procedures, production configurations

### Examples of Manual Testing Scenarios

#### GitHub Actions Workflows
- **Testing need**: Workflows triggered by real GitHub events (pull_request, issues, etc.)
- **Why manual**: Webhook payloads from GitHub cannot be perfectly simulated locally
- **How to test**: See [Testing GitHub Actions Workflows](#testing-github-actions-workflows)

#### UI/UX Changes
- **Testing need**: Visual verification of layout, styling, responsive behavior
- **Why manual**: Automated tests cannot verify visual appearance or user experience
- **How to test**: Manual review in browser, multiple screen sizes, accessibility tools

#### Authentication Flows
- **Testing need**: OAuth callbacks, token handling, session management
- **Why manual**: Requires real credentials and third-party services
- **How to test**: End-to-end flow with real authentication provider

#### External API Integrations
- **Testing need**: API calls to real external services
- **Why manual**: Cannot reliably mock all edge cases and behaviors
- **How to test**: Integration testing with real API endpoints (test/staging environment)

#### Performance Characteristics
- **Testing need**: Response times, resource usage, scalability
- **Why manual**: Requires real-world load and environment conditions
- **How to test**: Load testing tools in environment matching production

## Documenting Manual Testing Requirements in PRs

When creating a PR that requires manual testing:

### 1. Use the Testing Classification Section

The PR template includes a "Testing Classification" section. Fill it out completely:

```markdown
## Testing Classification

### Automated Tests
- [x] test_foo.py::test_new_feature - Added
- [x] test_bar.py - Existing tests still pass

### Manual Testing Required
- [ ] **Workflow: auto-grant-autonomy.yml** - Create issue with role label, verify agent:go added
- [ ] **Workflow: auto-assign-copilot.yml** - Add agent:go label, verify Copilot assigned

### Cannot Test (with justification)
- External webhook signatures - Requires GitHub's signing key
```

### 2. Add the `needs:manual-testing` Label

Add the `needs:manual-testing` label to the PR to signal reviewers that manual verification is required before merge.

### 3. Provide Clear Testing Instructions

For each item requiring manual testing, specify:
- **What to test**: Exact feature or behavior to verify
- **How to trigger**: Steps to reproduce the scenario
- **Expected outcome**: What should happen when successful
- **How to verify**: How to confirm the expected outcome

**Example:**
```markdown
- [ ] **Workflow: auto-grant-autonomy.yml**
  - Trigger: Create a new issue and add a `role:*` label
  - Expected: Issue automatically receives `agent:go` label within 30 seconds
  - Verify: Check issue labels in GitHub UI or via `gh issue view <issue-number>`
```

### 4. Document Test Results

After performing manual testing, update the PR with results:

```markdown
## Manual Testing Results

✅ **Workflow: auto-grant-autonomy.yml** - Tested successfully
- Created issue #123 with `role:swe` label
- Confirmed `agent:go` label added automatically within 15 seconds
- Workflow run: https://github.com/owner/repo/actions/runs/12345

✅ **Workflow: auto-assign-copilot.yml** - Tested successfully
- Added `agent:go` label to issue #124
- Confirmed @copilot assigned within 20 seconds
- Workflow run: https://github.com/owner/repo/actions/runs/12346
```

Once all manual testing is complete, add the `tested:manual` label and remove `needs:manual-testing`.

## Testing GitHub Actions Workflows

GitHub Actions workflows often require manual testing because they respond to real webhook events.

### Local Testing with `act`

The `act` tool allows running GitHub Actions locally:

```bash
# Install act
brew install act  # macOS
# or download from: https://github.com/nektos/act

# Run a workflow
act pull_request

# Run with specific event payload
act pull_request -e test/fixtures/pull_request.json

# Run specific job
act -j test
```

**Limitations:**
- Some GitHub context is not available (`secrets`, `github.token`)
- Webhook payloads may not match production exactly
- Some actions may not work in local Docker environment

**Best practice:** Use `act` for initial validation, but always test with real GitHub events before merge.

### Manual Trigger Testing

For workflows that support manual triggers (`workflow_dispatch`):

```yaml
on:
  workflow_dispatch:
    inputs:
      issue_number:
        description: 'Issue number to test'
        required: true
```

Test via GitHub UI or CLI:

```bash
# Via GitHub CLI
gh workflow run workflow-name.yml -f issue_number=123

# Check status
gh run watch

# View logs
gh run view --log
```

### Real Event Testing

For workflows triggered by GitHub events (issues, PRs, etc.):

1. **Create a test issue/PR** with a clear title indicating it's for testing
2. **Trigger the event** (add label, create comment, etc.)
3. **Monitor workflow execution** in Actions tab or via CLI:
   ```bash
   gh run list --workflow=workflow-name.yml
   gh run view <run-id> --log
   ```
4. **Verify expected behavior** (labels added, comments posted, etc.)
5. **Clean up** test artifacts (close test issue/PR, remove labels)

### Testing Checklist for Workflows

Before marking workflow testing complete:

- [ ] Workflow triggers on expected event
- [ ] Workflow has correct permissions configured
- [ ] Workflow completes successfully (green check)
- [ ] Workflow produces expected side effects (labels, comments, etc.)
- [ ] Workflow logs show expected behavior (no unexpected errors)
- [ ] Workflow handles error cases gracefully (if applicable)
- [ ] Test artifacts cleaned up (test issues/PRs closed)

## Testing UI/UX Changes

For visual changes, provide:

### 1. Screenshots

Include before/after screenshots in PR description:

```markdown
## Visual Changes

### Before
![Before](path/to/before.png)

### After
![After](path/to/after.png)
```

### 2. Responsive Design Testing

Test across viewport sizes:
- Mobile (320px, 375px, 414px)
- Tablet (768px, 1024px)
- Desktop (1280px, 1920px)

```markdown
- [ ] Tested on mobile viewports (320px, 375px, 414px)
- [ ] Tested on tablet viewports (768px, 1024px)
- [ ] Tested on desktop viewports (1280px, 1920px)
```

### 3. Browser Compatibility

Test in major browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest, if on macOS)
- Edge (latest)

```markdown
- [ ] Chrome (latest) - ✅ Works correctly
- [ ] Firefox (latest) - ✅ Works correctly
- [ ] Safari (latest) - ✅ Works correctly
- [ ] Edge (latest) - ✅ Works correctly
```

### 4. Accessibility Testing

Use accessibility tools to verify:
- Keyboard navigation
- Screen reader compatibility
- Color contrast ratios
- Focus indicators

```markdown
- [ ] Keyboard navigation works (Tab, Enter, Escape)
- [ ] Screen reader announces elements correctly
- [ ] Color contrast meets WCAG AA standards
- [ ] Focus indicators visible and clear
```

## Testing Authentication Flows

For OAuth or authentication changes:

### Setup
1. Register test application with OAuth provider
2. Configure test credentials (store in 1Password, not in repo)
3. Set up test environment with test credentials

### Testing Checklist
- [ ] Login flow completes successfully
- [ ] Tokens stored securely (not in browser console/local storage)
- [ ] Token refresh works correctly
- [ ] Logout clears all tokens and sessions
- [ ] Error handling works (invalid credentials, expired tokens)
- [ ] Redirect back to original page after login

### Documentation
Document test results with:
- OAuth provider used (e.g., "Tested with GitHub OAuth")
- Any edge cases discovered
- Known limitations or issues

## Testing External API Integrations

For integrations with external APIs:

### Setup
1. Use test/staging API endpoints (never production for testing)
2. Set up test API keys or credentials
3. Verify rate limits and quotas for test environment

### Testing Checklist
- [ ] Successful API calls return expected data
- [ ] Error handling works (network errors, rate limits, invalid responses)
- [ ] Timeouts handled gracefully
- [ ] Retry logic works correctly (if applicable)
- [ ] API keys/credentials not logged or exposed

### Documentation
Document:
- API endpoint used (test/staging URL)
- Rate limits or quotas encountered
- Any unexpected behaviors or edge cases
- Performance observations (response times, payload sizes)

## When Testing Cannot Be Done

Some functionality truly cannot be tested before merge:

### Legitimate Reasons
- Requires production credentials not available in test environments
- Depends on third-party webhook signatures or keys
- Production-only configuration or infrastructure
- Real user data or scenarios that cannot be simulated

### How to Handle
1. **Document in "Cannot Test" section** with clear justification
2. **Implement safeguards**: Feature flags, rollback procedures, monitoring
3. **Plan for post-merge validation**: Monitoring, canary deployment, staged rollout
4. **Accept the risk explicitly**: Get approval from project maintainer

```markdown
### Cannot Test (with justification)
- Production database migration - No test environment with production-scale data
  - Mitigation: Dry-run in staging, database backup before migration, rollback plan documented
- External webhook signatures - Requires third-party signing keys not available until production
  - Mitigation: Signature verification in test mode (skip validation), monitor production logs after deploy
```

## Labels for Testing Status

### `needs:manual-testing`
- **When to add**: PR includes functionality requiring manual verification
- **Who adds it**: PR author or reviewer identifying manual testing needs
- **When to remove**: After all manual testing completed and documented

### `tested:manual`
- **When to add**: All required manual testing completed successfully
- **Who adds it**: Person who performed the manual testing
- **Implies**: PR is ready for final review and merge (assuming CI also passes)

## Reviewer Checklist for Manual Testing

When reviewing a PR with manual testing requirements:

1. **Verify testing classification section is complete**
   - Automated tests listed
   - Manual testing requirements specified with clear instructions
   - Cannot-test items justified

2. **Check for `needs:manual-testing` label**
   - Present if manual testing required
   - Removed only after testing complete

3. **Verify manual testing was performed**
   - Test results documented in PR
   - Screenshots/logs provided where applicable
   - `tested:manual` label added

4. **Validate test results**
   - Results match expected outcomes
   - All required scenarios covered
   - Edge cases considered

5. **Approve only if**
   - All manual testing complete OR
   - Cannot-test justification acceptable with mitigation plan

## Local Agent Awareness

When a local agent (e.g., Kerrigan in VS Code) reviews a PR:

### Detection
Check for "Manual Testing Required" section in PR description:
```regex
### Manual Testing Required\n.*\[[ x]\]
```

### Prompt User
If manual testing is required and not yet complete:
1. Display list of manual testing items
2. Prompt user to perform tests
3. Wait for user confirmation before approving

### Record Completion
After user confirms testing:
1. Add comment documenting test completion
2. Add `tested:manual` label
3. Remove `needs:manual-testing` label
4. Proceed with approval if all other checks pass

## Best Practices

1. **Be specific**: Clearly describe what to test and how to verify
2. **Provide context**: Explain why manual testing is needed
3. **Document results**: Always record outcomes of manual tests
4. **Use labels**: Apply `needs:manual-testing` and `tested:manual` appropriately
5. **Test early**: Don't wait until PR is ready to merge to perform manual tests
6. **Clean up**: Remove test artifacts (test issues, test data) after testing
7. **Screenshots help**: Visual evidence of testing is valuable for reviewers
8. **Consider alternatives**: Always ask if automated testing is truly impossible

## Common Anti-Patterns to Avoid

❌ **"Manual testing required" with no specifics**
- Problem: Reviewer doesn't know what to test
- Solution: List specific test cases with instructions

❌ **Claiming "cannot test" without justification**
- Problem: May indicate untested code going to production
- Solution: Provide clear reason or implement tests

❌ **Manual testing only**
- Problem: No automated regression prevention
- Solution: Add automated tests wherever possible

❌ **Testing in production first**
- Problem: Risks breaking production environment
- Solution: Use test/staging environments when available

❌ **No documentation of test results**
- Problem: No evidence that testing was actually performed
- Solution: Document all manual test results in PR

## Related Documentation

- [PR Review Playbook](pr-review.md) - General PR review guidelines
- [Triage Playbook](triage.md) - PR pipeline management
- [GitHub Labels](../docs/github-labels.md) - Label definitions
- [Automation Limits](../docs/automation-limits.md) - What can/cannot be automated
- [Automation Testing](../docs/automation-testing.md) - Testing automation workflows

## See Also

- [act - Run GitHub Actions locally](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [WCAG Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
