# SDK Agent Service

This directory contains the SDK-based autonomous agent service that enables fully automated issue-to-PR workflows.

## Overview

The SDK Agent Service is triggered automatically when issues are labeled with `agent:go`, `agent:sprint`, or `autonomy:override`. It:

1. Validates autonomy gates
2. Determines the appropriate agent role based on labels
3. Executes the agent using GitHub Copilot SDK
4. Creates a pull request with the results
5. Posts status updates to the issue

## Architecture

```
Issue Event → GitHub Actions → SDK Agent Service → Copilot SDK → PR Created
                    ↓                    ↓                ↓
              Webhook Handler      Agent Orchestrator   Status Reporter
              GitHub App Auth      SDK Client           PR Creator
```

## Setup

### Prerequisites

1. **GitHub App** with the following permissions:
   - Repository permissions:
     - Contents: Read & write
     - Issues: Read & write
     - Pull requests: Read & write
     - Metadata: Read

2. **GitHub Secrets** configured:
   - `SDK_AGENT_APP_ID`: Your GitHub App ID
   - `SDK_AGENT_PRIVATE_KEY`: Your GitHub App private key (PEM format)

### Installation

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm test
```

## Usage

### Local Development

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run the service
npm run dev -- \
  --event-type "issues.labeled" \
  --issue-number 128 \
  --repository "Kixantrix/kerrigan"
```

### Production (GitHub Actions)

The service runs automatically via the `.github/workflows/sdk-agent-service.yml` workflow when:

1. An issue is labeled with `agent:go`, `agent:sprint`, or `autonomy:override`
2. An issue is assigned and has one of those labels

No manual triggering is required.

## Agent Roles

The service supports multiple agent roles, determined by issue labels:

| Label | Role | Prompt File | Description |
|-------|------|-------------|-------------|
| `role:spec` | Spec | `kickoff-spec.md` | Define project goals and acceptance criteria |
| `role:architect` | Architect | `architecture-design.md` | Design system architecture |
| `role:swe` | SWE | `implementation-swe.md` | Implement features with tests |
| `role:deploy` | Deploy | `deployment-ops.md` | Create operational runbooks |
| `role:security` | Security | `security-review.md` | Security review and hardening |
| `role:triage` | Triage | `triage-analysis.md` | Analyze and categorize issues |

If no role label is present, it defaults to SWE.

## Autonomy Gates

The service respects Kerrigan's autonomy gates:

- ✅ `agent:go`: Single-issue approval
- ✅ `agent:sprint`: Sprint-mode approval
- ✅ `autonomy:override`: Override for exceptional cases
- ❌ No label: Service will not process the issue

## Status Updates

The service posts comments to issues with status updates:

1. **Started**: When the agent begins work
2. **Success**: When a PR is created successfully
3. **Failure**: When an error occurs, with retry instructions
4. **Progress**: Periodic updates during long-running tasks

## Error Handling

Common errors and solutions:

### Authentication Failed
- Verify `SDK_AGENT_APP_ID` and `SDK_AGENT_PRIVATE_KEY` are correct
- Ensure GitHub App is installed on the repository
- Check that the private key hasn't expired

### SDK Timeout
- Increase `SDK_TIMEOUT_MS` in environment variables
- Check Copilot SDK service availability
- Verify network connectivity

### PR Creation Failed
- Check for branch name conflicts
- Verify write permissions on the repository
- Ensure no existing PR for the same issue

### SDK Integration Not Implemented
- This is expected until PR #127 is merged
- The service structure is ready; SDK calls are placeholders
- See `src/sdk-client.ts` for implementation details

## File Structure

```
services/sdk-agent/
├── src/
│   ├── index.ts                # Main entry point and CLI
│   ├── types.ts                # TypeScript type definitions
│   ├── github-app-auth.ts      # GitHub App authentication
│   ├── agent-orchestrator.ts   # Role routing and autonomy gates
│   ├── sdk-client.ts           # Copilot SDK wrapper (placeholder)
│   ├── pr-creator.ts           # Pull request creation
│   └── status-reporter.ts      # Issue status comments
├── tests/                      # Unit tests
├── package.json                # Dependencies and scripts
├── tsconfig.json               # TypeScript configuration
├── .env.example                # Example environment variables
└── README.md                   # This file
```

## Development

### Running Tests

```bash
npm test
```

### Linting

```bash
npm run lint
```

### Formatting

```bash
npm run format
```

## Monitoring

Monitor the service through:

1. **GitHub Actions Logs**: Check workflow runs in the Actions tab
2. **Issue Comments**: Service posts updates to issues
3. **Pull Requests**: Successful runs create PRs automatically

## Cost Considerations

### GitHub Actions

- **Public repositories**: FREE (unlimited minutes)
- **Private repositories**: 
  - Free tier: 2,000 minutes/month
  - Additional: $0.008/minute
  - Estimated per-issue: 5-10 minutes = $0.04-$0.08

### Copilot SDK

- API usage charges may apply
- Monitor actual costs in pilot phase
- Set up cost alerts if available

## Security

### Secret Management

- ✅ GitHub App private key stored in GitHub Secrets
- ✅ Never logged or exposed in outputs
- ✅ Tokens refresh automatically (1-hour lifetime)
- ✅ Minimum required permissions

### Code Execution

- ✅ Runs in isolated GitHub Actions runner
- ✅ No execution of arbitrary user code
- ✅ All changes go through PR review

### Audit Trail

- ✅ All actions logged to issue comments
- ✅ GitHub Actions logs retained (90 days)
- ✅ Git history tracks all changes

## Troubleshooting

### Service doesn't start

1. Check that the issue has an autonomy gate label
2. Verify GitHub App is installed on the repository
3. Check GitHub Actions workflow is enabled

### Authentication errors

1. Verify secrets are set correctly in repository settings
2. Check GitHub App permissions
3. Ensure private key is in correct PEM format

### SDK errors

1. Currently expected - SDK integration pending PR #127
2. Check logs for specific error messages
3. Verify Copilot API availability

## Future Enhancements

- [ ] Full Copilot SDK integration (pending PR #127)
- [ ] Support for custom agent prompts
- [ ] Enhanced context injection (specs, architecture)
- [ ] Multi-repository orchestration
- [ ] Cost tracking and analytics
- [ ] Advanced error recovery
- [ ] Status dashboard integration

## Related Documentation

- [SDK Architecture Proposal](../../docs/sdk-architecture-proposal.md)
- [Kerrigan Architecture](../../docs/architecture.md)
- [Automation Limits](../../docs/automation-limits.md)
- [Agent Assignment](../../docs/agent-assignment.md)

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review GitHub Actions logs for errors
3. Open an issue in the Kerrigan repository
4. Tag with `sdk-agent-service` label

---

**Status**: ⚠️ Placeholder Implementation - Awaiting SDK Integration (PR #127)
**Last Updated**: 2026-01-25
