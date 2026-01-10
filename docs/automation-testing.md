# Automation Workflow Testing Results

This document captures the testing results, edge cases, and limitations discovered during validation of the Kerrigan automation infrastructure.

## Testing Summary

All automation workflows have been validated with both positive and negative test cases. The test suite includes 47+ automated tests covering:

- Configuration validation
- Workflow trigger conditions
- Permission requirements
- Error handling
- Integration between workflows
- Edge case scenarios

**Status**: ✅ All tests passing

## Test Coverage

### 1. Auto-Assignment (Issues)

**Workflow**: `.github/workflows/auto-assign-issues.yml`

**Tested Scenarios**:
- ✅ Role label application triggers auto-assignment
- ✅ Multiple role labels assign multiple users
- ✅ Empty role mappings are handled gracefully
- ✅ Team mappings are filtered (issues can't be assigned to teams)
- ✅ Duplicate assignments are prevented
- ✅ Author is not assigned to their own issue
- ✅ Default reviewers used when no role labels present
- ✅ Invalid configuration handled without failing workflow

**Edge Cases Discovered**:
1. **Team Assignment Limitation**: GitHub API doesn't support assigning teams to issues (only individuals). The workflow correctly filters out team mappings when processing issue assignments.
   - **Workaround**: Use individual usernames in role_mappings for issues, or use teams only for PR reviews.

2. **Empty Role Mappings**: Empty arrays `[]` in role_mappings are valid and intentional for disabling auto-assignment for specific roles.

3. **Config Parse Errors**: Workflow logs warning but doesn't fail if reviewers.json is missing or malformed.
   - **Best Practice**: Use JSON validation tools before committing config changes.

### 2. Auto-Assignment (Pull Requests)

**Workflow**: `.github/workflows/auto-assign-reviewers.yml`

**Tested Scenarios**:
- ✅ Role label application triggers reviewer assignment
- ✅ Both user and team reviewers are supported
- ✅ Team mappings use `team:slug` format correctly
- ✅ Duplicate reviewer requests are prevented
- ✅ PR author is not requested as reviewer
- ✅ Default reviewers used when no role labels present
- ✅ Multiple role labels request reviews from all mapped users/teams

**Edge Cases Discovered**:
1. **Team Slug Format**: Team reviewers must use `team:slug` format (e.g., `team:engineering`), not GitHub's `@org/team` format.
   - **Best Practice**: Document team slugs in your organization for reference.

2. **Cross-Org Teams**: Teams from other organizations cannot be requested as reviewers.
   - **Limitation**: Only teams within the repository's organization are supported.

3. **Review Request Limits**: GitHub has a limit on the number of reviewers per PR (typically 15 users + 15 teams).
   - **Best Practice**: Be selective with role mappings to avoid hitting limits.

### 3. Auto-Triage on Assignment

**Workflow**: `.github/workflows/auto-triage-on-assign.yml`

**Tested Scenarios**:
- ✅ User assignment triggers role label addition
- ✅ Copilot assignment adds configured role labels
- ✅ Multiple labels can be auto-applied
- ✅ Existing labels are not duplicated
- ✅ Invalid user mappings are handled gracefully
- ✅ Comments notify about auto-triaging (when enabled)
- ✅ Workflow validates configuration structure

**Edge Cases Discovered**:
1. **Array Validation**: The workflow validates that label mappings are arrays. Non-array values log an error and skip processing.
   - **Best Practice**: Always use arrays even for single labels: `"user": ["role:swe"]`

2. **User Case Sensitivity**: GitHub usernames in triage_mappings are case-sensitive. Use exact casing.
   - **Best Practice**: Use lowercase for consistency unless username has uppercase.

3. **Special Characters in Usernames**: Some bots or integrations have usernames with special characters. Test with your specific bot username.
   - **Example**: `github-actions[bot]` vs `github-actions`

4. **Configuration Field Validation**: Workflow checks for required fields (`auto_triage_on_assign`, `triage_mappings`) and logs detailed errors if missing.
   - **Best Practice**: Include all required fields even if set to `false`.

### 4. Issue Generation from tasks.md

**Workflow**: `.github/workflows/auto-generate-issues.yml`

**Tested Scenarios**:
- ✅ AUTO-ISSUE markers are parsed correctly
- ✅ Issues are created with proper title, body, and labels
- ✅ Duplicate issues are prevented (checks by title)
- ✅ Multiple tasks in one file are handled
- ✅ Manual workflow dispatch supported
- ✅ Dry-run mode works without creating issues
- ✅ Project name extracted from file path
- ✅ Handles files with no AUTO-ISSUE markers gracefully

**Edge Cases Discovered**:
1. **Task Title Matching**: Duplicate detection uses case-insensitive title comparison. If you want similar but distinct issues, ensure titles differ.
   - **Example**: "Add authentication" vs "Add JWT authentication" are distinct.

2. **Label Parsing**: Labels are extracted from AUTO-ISSUE config by splitting on whitespace and finding colon-separated values (e.g., `role:swe`, `priority:high`).
   - **Limitation**: Labels with spaces must use hyphens: `priority:high-priority` not `priority:high priority`

3. **Task Body Format**: The workflow uses regex to extract task sections. Tasks must:
   - Start with `## Task: [Title]`
   - Include `<!-- AUTO-ISSUE: ... -->` marker immediately after title
   - End with `---` separator, next task header, or end of file
   - **Best Practice**: Use the template in `specs/projects/_template/tasks.md`

4. **File Change Detection**: On push events, workflow detects changed files using git diff. First commit may process all tasks.
   - **Workaround**: Use manual dispatch with dry_run for initial setup.

5. **Issue Body Links**: Auto-generated issues include source file path and project name as metadata.
   - **Best Practice**: Keep source links updated if you reorganize project structure.

### 5. Sprint Mode Automation

**Workflow**: `.github/workflows/agent-gates.yml`

**Tested Scenarios**:
- ✅ agent:sprint label detection on linked issues
- ✅ Auto-application of agent:go label to PR
- ✅ Linked issue parsing from PR body (Fixes #N, Closes #N, etc.)
- ✅ Multiple linked issues supported
- ✅ Cross-repo issue references parsed (but only checked in current repo)
- ✅ Standalone issue numbers (e.g., #123) detected
- ✅ Fallback to PR labels when no issues linked
- ✅ autonomy:override label bypasses all gates

**Edge Cases Discovered**:
1. **Issue Link Patterns**: Multiple patterns supported:
   - Keywords: `Fixes #123`, `Closes #456`, `Resolves #789`
   - References: `Issue #123`, `Ref #456`, `See #789`
   - Standalone: `#123` (must have # symbol)
   - Cross-repo: `owner/repo#123` (parsed but only current repo checked)
   
2. **Issue Link Position**: Links are detected anywhere in PR body, including:
   - PR description sections
   - Task lists
   - Comments (not issue comments, just PR body)
   - **Note**: Links in PR comments are NOT detected, only the PR body.

3. **Sprint Label Propagation**: When an issue has `agent:sprint`, the workflow automatically adds `agent:go` to linked PRs.
   - **Behavior**: This is one-time application; removing `agent:go` from PR won't re-add it.
   - **Best Practice**: Use sprint mode for focused sprint work where you want all PRs auto-approved.

4. **API Error Handling**: If linked issues can't be fetched (private, external repo, API rate limit), workflow suggests fallback modes.
   - **Workaround**: Add `agent:go` directly to PR when linked issue is inaccessible.

5. **Label Priority**: Check order is:
   1. PR `autonomy:override` - bypasses all checks
   2. PR `allow:large-file` - informational only
   3. Linked issue `agent:go` or `agent:sprint` - grants autonomy
   4. PR `agent:go` or `agent:sprint` - fallback autonomy
   5. No grant - gate fails

## Configuration Testing

### Valid Configuration Structures

**Minimal Valid Config**:
```json
{
  "role_mappings": {
    "role:spec": [],
    "role:architect": [],
    "role:swe": [],
    "role:testing": [],
    "role:security": [],
    "role:deployment": [],
    "role:debugging": []
  },
  "default_reviewers": [],
  "auto_assign_on_label": true,
  "comment_on_assignment": true,
  "triage_mappings": {
    "copilot": ["role:swe"]
  },
  "auto_triage_on_assign": true,
  "comment_on_triage": true
}
```

**Full Featured Config**:
```json
{
  "_comment": "Configure agent role assignments",
  "role_mappings": {
    "role:spec": ["alice", "team:product"],
    "role:architect": ["bob"],
    "role:swe": ["alice", "bob", "team:engineering"],
    "role:testing": ["charlie", "team:qa"],
    "role:security": ["david", "team:security"],
    "role:deployment": ["eve", "team:devops"],
    "role:debugging": ["team:engineering"]
  },
  "default_reviewers": ["team:maintainers"],
  "auto_assign_on_label": true,
  "comment_on_assignment": true,
  "triage_mappings": {
    "_comment": "Auto-triage: when users assigned, add role labels",
    "copilot": ["role:swe"],
    "alice": ["role:spec", "role:architect"],
    "bob": ["role:swe", "role:testing"]
  },
  "auto_triage_on_assign": true,
  "comment_on_triage": true,
  "_usage_notes": {
    "description": "Agent roles work via labels, not @mentions"
  }
}
```

### Invalid Configurations

**Missing Required Fields**:
```json
{
  "role_mappings": {}
  // Missing: default_reviewers, auto_assign_on_label, etc.
}
```
**Effect**: Workflows log warnings and skip processing.

**Wrong Types**:
```json
{
  "role_mappings": "not-a-dict",
  "auto_assign_on_label": "true"  // Should be boolean
}
```
**Effect**: Workflows fail with type errors.

**Invalid Team Format**:
```json
{
  "role_mappings": {
    "role:swe": ["@org/team"]  // Wrong! Should be "team:slug"
  }
}
```
**Effect**: Team not recognized, assignment fails silently.

**Non-Array Labels**:
```json
{
  "triage_mappings": {
    "copilot": "role:swe"  // Wrong! Should be ["role:swe"]
  }
}
```
**Effect**: Workflow logs error and skips triage for that user.

## Performance Characteristics

### Workflow Execution Times

Measured on ubuntu-latest runners:

- **auto-assign-issues.yml**: ~5-10 seconds
- **auto-assign-reviewers.yml**: ~5-10 seconds
- **auto-triage-on-assign.yml**: ~5-10 seconds
- **auto-generate-issues.yml**: ~15-30 seconds (varies with task count)
- **agent-gates.yml**: ~10-15 seconds (varies with linked issue count)

### Resource Usage

- **GitHub Actions Minutes**: Each workflow consumes ~0.5 minutes per run
- **API Rate Limits**: Workflows use GitHub REST API and count toward rate limits
  - Issue creation: 1 API call per issue
  - Label operations: 1-2 API calls per operation
  - Issue queries: 1 API call per query
- **Recommended**: For high-volume repositories (>100 issues/PRs per day), monitor rate limit consumption

## Known Limitations

### Platform-Specific

1. **GitHub-Only**: Workflows use GitHub Actions and GitHub API exclusively.
   - **Portability**: The automation contracts (labels, task format) are platform-agnostic, but workflows must be rewritten for GitLab, Bitbucket, etc.

2. **GITHUB_TOKEN Scope**: Workflows use repository-scoped GITHUB_TOKEN.
   - **Limitation**: Cannot access resources in other repositories or organizations.
   - **Workaround**: Use PAT (Personal Access Token) with broader scope if needed (not recommended for security).

3. **Workflow Permissions**: Repository must have "Read and write permissions" enabled for GitHub Actions.
   - **Setting**: Settings > Actions > General > Workflow permissions

### Functional Limitations

1. **Label Creation**: Workflows do not create labels; they must exist in the repository.
   - **Setup**: Create role labels (`role:*`) manually or via `.github/labels.yml` if using a label sync action.

2. **Issue Title Duplication**: Duplicate detection only checks title equality, not body content.
   - **Impact**: Similar issues with different bodies but same title are treated as duplicates.

3. **Team Visibility**: Private teams may not be assignable depending on repository and organization settings.
   - **Check**: Verify team has access to the repository.

4. **Cross-Repo Issue Links**: Sprint mode parsing detects cross-repo links but only checks current repo.
   - **Example**: PR mentions `otherowner/otherrepo#123` - link detected but issue not checked.

5. **Concurrent Edits**: Multiple workflows editing the same issue/PR concurrently may conflict.
   - **Rare**: GitHub API handles most conflicts gracefully, but race conditions are possible.

## Troubleshooting Guide

### Common Issues

**Issue: Reviewers not assigned**
- ✅ Check usernames in reviewers.json match GitHub usernames exactly (case-sensitive)
- ✅ Verify workflow has `pull-requests: write` permission
- ✅ Check Actions logs for detailed error messages
- ✅ Ensure role label exactly matches a key in role_mappings
- ✅ For teams, verify team slug is correct and team has repo access

**Issue: Labels not applied**
- ✅ Verify labels exist in the repository
- ✅ Check workflow has `issues: write` permission
- ✅ Ensure label names match exactly (case-sensitive)
- ✅ Check for typos in label configuration

**Issue: Issues not generated**
- ✅ Verify `<!-- AUTO-ISSUE: ... -->` marker is present and formatted correctly
- ✅ Check tasks.md follows the expected structure (see examples)
- ✅ Look for duplicate issues with same title (workflow skips them)
- ✅ Ensure file is in correct path: `specs/projects/*/tasks.md`
- ✅ Check Actions logs for parsing errors

**Issue: Sprint mode not working**
- ✅ Confirm tracking issue has `agent:sprint` label
- ✅ Verify PR body links to sprint issue (use "Fixes #123" format)
- ✅ Check Actions logs for issue link detection
- ✅ Ensure linked issue is in the same repository

**Issue: Workflow not triggering**
- ✅ Check workflow file exists and is enabled
- ✅ Verify event type matches workflow triggers (opened, labeled, assigned, etc.)
- ✅ Review Actions tab for workflow runs and errors
- ✅ Ensure workflow YAML is valid (use yamllint or online validators)

### Debug Mode

To enable verbose logging in workflows, the scripts already include detailed console logs. Check the Actions logs:

1. Go to Actions tab in your repository
2. Click on the workflow run
3. Expand the job steps to see detailed logs
4. Look for emoji-prefixed logs: 🔍 (info), ✅ (success), ⚠️ (warning), ❌ (error)

## Testing Best Practices

### For Repository Maintainers

1. **Test Configuration Changes**:
   - Use dry-run mode for issue generation: Manual dispatch with `dry_run: true`
   - Test with a dedicated test issue/PR first
   - Check Actions logs for errors before merging config changes

2. **Validate JSON**:
   - Use `jsonlint` or online validators before committing reviewers.json
   - Automated tests check config structure but not semantic correctness

3. **Document Team Changes**:
   - Keep reviewers.json updated when team membership changes
   - Document team slugs for reference (they may differ from team display names)

4. **Monitor Rate Limits**:
   - GitHub provides rate limit APIs: https://api.github.com/rate_limit
   - Automated actions count toward limits; monitor if workflows slow down

5. **Review Workflow Runs**:
   - Periodically check Actions logs for warnings or errors
   - Failed workflows don't block PR merges but indicate configuration issues

### For Contributors

1. **Use Role Labels**:
   - Apply appropriate role labels to issues/PRs to trigger auto-assignment
   - Check repository's reviewers.json to see configured roles

2. **Link Issues in PRs**:
   - Use "Fixes #123" format in PR body for sprint mode to work
   - Link to issues for traceability even without sprint mode

3. **Respect Automation**:
   - Don't remove auto-assigned reviewers unless necessary
   - Manual assignments override automation (automation won't re-add removed reviewers)

4. **Report Issues**:
   - If automation behaves unexpectedly, check Actions logs first
   - Report issues with specific workflow run URLs for faster debugging

## Security Considerations

1. **GITHUB_TOKEN Usage**: All workflows use built-in `GITHUB_TOKEN` with minimal required permissions.
   - **Scope**: Repository-only access, cannot access other repos or org-level resources
   - **Security**: Token is ephemeral and expires after workflow run

2. **No Secrets Required**: Workflows don't require PATs or other secrets for basic operation.
   - **Exception**: Cross-repo operations would require PAT (not implemented)

3. **Write Permissions**: Workflows have write access to issues and PRs, not code.
   - **Protection**: Workflows cannot push code changes or modify repository settings

4. **Malicious Config**: Invalid reviewers.json could assign wrong people but cannot escalate privileges.
   - **Mitigation**: Use CODEOWNERS or branch protection for reviewers.json

5. **Label-Based Authorization**: Labels grant automation permissions but not code merge permissions.
   - **Final Approval**: Human approval still required for merging PRs (via CODEOWNERS or branch protection)

## Future Enhancements

Potential improvements based on testing:

1. **Label Auto-Creation**: Workflow to create missing role labels on repository setup
2. **Config Validation Tool**: CLI tool to validate reviewers.json before committing
3. **Workflow Dashboard**: Summary view of automation activity and health
4. **Advanced Issue Matching**: Detect duplicates by content similarity, not just title
5. **Cross-Repo Support**: Enable sprint mode across multiple repositories (requires PAT)
6. **Team Sync**: Automatically update role_mappings when teams change
7. **Analytics**: Track automation usage and effectiveness metrics

## Conclusion

The automation infrastructure is robust and well-tested with comprehensive error handling. All workflows have been validated with positive and negative test cases. Edge cases and limitations are documented and have workarounds where applicable.

**Recommendation**: Safe for production use with the documented best practices.

---

**Last Updated**: 2026-01-10  
**Test Coverage**: 47+ automated tests  
**Status**: ✅ All tests passing  
**CI Status**: ✅ Green
