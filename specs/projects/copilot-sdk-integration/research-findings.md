# Copilot SDK/CLI Research Findings

**Date**: 2026-01-27  
**Status**: Investigation Complete  
**Investigator**: Kerrigan SDK Agent Prototype

## Executive Summary

The GitHub Copilot SDK is a **programmatic interface to the Copilot CLI**, not a direct API to GitHub's AI services. It requires:

1. **Copilot CLI installed** on the machine running the SDK
2. **User authenticated** with a Copilot subscription (via OAuth/CLI auth)
3. **Premium request quota** from the user's Copilot subscription

This architecture means **fully autonomous CI-triggered agents are not directly supported** out-of-the-box. However, there are viable paths forward.

## Architecture Understanding

### What We Initially Assumed
```
GitHub App → SDK → Copilot API → AI Response
```

### What It Actually Is
```
Your Application
       ↓
  SDK Client (npm @github/copilot-sdk)
       ↓ JSON-RPC
  Copilot CLI (server mode) ← Requires CLI installed + user auth
       ↓
  GitHub Copilot Service (uses user's subscription quota)
```

### Key Insight
The SDK is a **wrapper around the Copilot CLI**, not a standalone API client. It:
- Spawns or connects to the CLI running in server mode
- Communicates via JSON-RPC over stdio or TCP
- Uses the CLI's authentication (user's Copilot subscription)

## Capability Assessment

### What the SDK Can Do ✅

| Capability | Status | Notes |
|------------|--------|-------|
| Programmatic prompts | ✅ | Full `sendAndWait()` API |
| Streaming responses | ✅ | Real-time token streaming |
| Custom tools | ✅ | Define tools SDK can call back |
| MCP integration | ✅ | Connect to MCP servers |
| Multiple models | ✅ | gpt-5, claude-sonnet-4.5, etc. |
| Session management | ✅ | Infinite sessions with compaction |
| Custom system prompts | ✅ | `systemMessage` config |
| File attachments | ✅ | Send files as context |
| Custom agents | ✅ | Define persona/behavior |
| Image support | ✅ | Image analysis |

### What the SDK Cannot Do ❌

| Limitation | Impact | Details |
|------------|--------|---------|
| GitHub App auth | High | Cannot use App installation tokens |
| Service account mode | High | Requires individual user subscription |
| CI-native execution | High | Needs CLI installed on runner |
| Webhook-triggered automation | Medium | Requires auth cache or user interaction |
| Rate limit independence | Medium | Uses user's premium request quota |

## Research Questions Answered

### 1. SDK Capabilities
- **API surface**: Full session management, streaming, tools, MCP
- **Programmatic invocation**: ✅ Yes, via Node.js/Python/Go/.NET SDKs
- **Authentication**: CLI's OAuth flow (user subscription required)
- **CI/CD environments**: ⚠️ Possible but requires auth caching
- **Rate limits**: Per-user premium request quota

### 2. CLI Capabilities
- **Server mode**: `copilot --server --port 4321` for external connections
- **Non-interactive**: SDK handles all interaction
- **Code generation**: Full agentic capabilities (file edits, git ops, web)
- **Issue → PR**: Theoretically possible with proper prompting
- **Authentication**: `gh auth login` + `gh extension install github/gh-copilot`

### 3. Integration Opportunities

| Scenario | Feasibility | Notes |
|----------|-------------|-------|
| Auto-trigger on issue label | ⚠️ Partial | Needs self-hosted runner with cached auth |
| PR creation from specs | ✅ Yes | SDK can invoke CLI's file/git tools |
| Automated code review | ✅ Yes | Feed PR diff as context |
| Test generation | ✅ Yes | SDK supports code generation |

### 4. Security & Compliance
- **Permissions**: User's Copilot permissions apply
- **Human-in-loop**: User must be authenticated (inherent gate)
- **Audit trail**: Session events, CLI logs
- **Enterprise controls**: Copilot policies apply

### 5. Custom Extensions & Agents
- **Custom agents**: ✅ Via `customAgents` session config
- **Context access**: ✅ File attachments + infinite sessions
- **Custom instructions**: ✅ System message customization
- **Distribution**: Via npm/pip packages wrapping SDK

### 6. Context & Knowledge
- **Project context**: ✅ File attachments, session state
- **RAG/Knowledge base**: ⚠️ Not built-in, but MCP servers could provide
- **Few-shot examples**: Via system message or attachments
- **Context management**: Infinite sessions with auto-compaction

### 7. Advanced Capabilities
- **MCP support**: ✅ Native MCP server integration
- **External tools**: ✅ Custom tool definitions with handlers
- **Multi-turn**: ✅ Session maintains conversation history
- **Agent chaining**: ⚠️ Manual orchestration needed
- **Observability**: Session events, streaming responses

## Paths Forward

### Option A: Self-Hosted Runner with Cached Auth
**Approach**: Deploy a self-hosted GitHub Actions runner with CLI pre-authenticated.

```yaml
# Workflow would run on self-hosted runner
runs-on: self-hosted
steps:
  - uses: actions/checkout@v4
  - name: Run Copilot Agent
    run: node sdk-agent/index.js
```

**Pros**:
- Works with current SDK
- Full agent capabilities

**Cons**:
- Requires infrastructure maintenance
- Auth token management
- Single-user bottleneck

### Option B: MCP + Direct LLM APIs
**Approach**: Use MCP (Model Context Protocol) with direct LLM API calls (OpenAI, Anthropic, etc.) and GitHub MCP server for repo operations.

```typescript
// Direct LLM call with MCP tools
const session = await createSession({
  model: "gpt-4o",
  mcpServers: {
    github: { type: "http", url: "https://api.githubcopilot.com/mcp/" }
  }
});
```

**Pros**:
- No CLI dependency
- API key authentication (service accounts)
- Better for CI/CD

**Cons**:
- Requires LLM API key management
- Different rate limits/costs
- Less "Copilot-native"

### Option C: Copilot Extensions (Future)
**Approach**: Build GitHub Copilot Extensions that respond to repository events.

**Pros**:
- Native GitHub integration
- Event-driven architecture
- Potential for OAuth app pattern

**Cons**:
- Feature maturity unknown
- May have same auth limitations

### Option D: Hybrid Human-Triggered
**Approach**: Keep human in the loop for Copilot invocation but automate everything else.

```
Issue Created → [Automated] Setup Branch, Gather Context
                    ↓
Human Reviews → [Manual] Trigger Copilot in IDE/Web
                    ↓
PR Created → [Automated] Run Tests, Request Review
```

**Pros**:
- Works today
- Maintains human oversight
- No infrastructure changes

**Cons**:
- Not fully autonomous
- Manual step required

## Recommendation

### Short-term (Now): Option D - Hybrid
Continue current workflow but enhance automation around the Copilot invocation:
- Automate context gathering
- Automate branch creation
- Automate PR formatting and review requests

### Medium-term (Q2 2026): Option A - Self-Hosted Runner
If fully autonomous agents are critical:
- Set up self-hosted runner with Copilot CLI
- Cache authentication with regular refresh
- Build SDK agent service

### Long-term (Q3+ 2026): Option B or C
Watch for:
- MCP + direct LLM APIs becoming more mature
- Copilot Extensions supporting webhook patterns
- GitHub announcing service account support for Copilot

## Implementation if Proceeding with Option A

### Prerequisites
1. Self-hosted runner with persistent storage
2. Machine user with Copilot license
3. CLI installed and authenticated
4. Secure token storage

### Architecture
```
GitHub Issue (labeled) 
    → GitHub Actions Workflow
    → Self-hosted Runner
    → SDK Agent Service
    → Copilot CLI (server mode)
    → Creates Branch/PR
```

### Estimated Effort
- Infrastructure setup: 2-3 days
- SDK agent service completion: 3-5 days
- Testing and hardening: 3-5 days
- Documentation: 1-2 days
- **Total**: ~2 weeks

### Cost Considerations
- Self-hosted runner: Infrastructure costs
- Copilot subscription: $19-39/user/month
- Premium requests: Based on usage
- GitHub API: Standard rate limits apply

## Files Modified During Investigation

### Created
- `services/sdk-agent/` - Prototype SDK agent service
- `docs/sdk-agent-*.md` - Investigation documentation

### Key Learnings Captured
- SDK requires CLI as backend
- Authentication is user-based, not App-based
- Full agentic capabilities available once authenticated
- MCP integration opens interesting possibilities

## Next Steps

1. **Decision needed**: Which path to pursue (A, B, C, or D)?
2. **If Option A**: Scope infrastructure requirements
3. **If Option D**: Document enhanced hybrid workflow
4. **Either way**: Update automation-limits.md with findings

## References

- [GitHub Copilot SDK Repository](https://github.com/github/copilot-sdk)
- [SDK Getting Started Guide](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md)
- [SDK Node.js Reference](https://github.com/github/copilot-sdk/blob/main/nodejs/README.md)
- [Copilot CLI Installation](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
