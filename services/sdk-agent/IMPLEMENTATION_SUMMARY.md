# SDK Agent Personas - Implementation Summary

## Overview

This implementation adds custom Kerrigan agent personas using the GitHub Copilot SDK's `systemMessage`, `customAgents`, and `tools` features. Each agent role now has specific prompts, tools, and behaviors aligned with Kerrigan conventions.

## Architecture

```
GitHub Issue (with labels)
    ↓
AgentOrchestrator.determineRole()
    ↓
SDKClient.executeAgent(context)
    ↓
getAgentConfig(role)
    ↓
loadPrompt(promptFile) + buildSystemMessage()
    ↓
SDK session creation with:
    - systemMessage (agent prompt + constitution)
    - tools (role-specific tool array)
    - model (gpt-4o)
    ↓
Agent execution with custom tools available
    ↓
Result returned to create PR
```

## Components

### 1. Agent Configurations (`src/agents/`)

**Files:**
- `index.ts` - KERRIGAN_AGENTS definitions
- `types.ts` - AgentConfig interface
- `prompt-loader.ts` - Utility functions
- `README.md` - Documentation

**Structure:**
```typescript
KERRIGAN_AGENTS = {
  spec: {
    name: 'kerrigan-spec',
    displayName: 'Kerrigan Spec Agent',
    promptFile: 'kickoff-spec.md',
    label: 'role:spec',
    tools: [readConstitutionTool, listArtifactsTool]
  },
  // ... 5 more agents
}
```

### 2. Custom Tools (`src/tools/`)

**Files:**
- `read-constitution.ts` - Reads specs/constitution.md
- `read-spec.ts` - Reads project specifications
- `list-artifacts.ts` - Lists project artifacts
- `index.ts` - Exports all tools

**Tool Structure:**
```typescript
{
  name: 'tool_name',
  description: 'What the tool does',
  parameters: z.object({ /* zod schema */ }),
  handler: async (params) => { /* implementation */ }
}
```

### 3. SDK Type Definitions (`src/copilot-sdk.d.ts`)

Added types for:
- `SystemMessage` - Custom system prompts
- `CustomAgent` - Agent configurations
- `Tool<T>` - Tool definitions with zod validation
- `SessionConfig` - Extended with systemMessage, customAgents, tools

### 4. SDK Client Integration (`src/sdk-client.ts`)

**Changes:**
1. Import agent configurations and prompt loader
2. Load agent config based on role: `getAgentConfig(context.role)`
3. Build system message: `buildSystemMessage(role, prompt, constitution)`
4. Create session with agent-specific configuration:
   ```typescript
   await client.createSession({
     model: 'gpt-4o',
     systemMessage: { content: systemMessageContent },
     tools: agentConfig.tools
   });
   ```

## Workflow

### Issue Processing Flow

1. **Issue Event Triggered**
   - GitHub issue labeled with `role:*` and `agent:go`
   - Workflow calls SDK Agent Service

2. **Role Determination**
   - `AgentOrchestrator.determineRole(labels)` maps label to role
   - Returns AgentRole with name, promptFile, description

3. **Agent Configuration Loading**
   - `getAgentConfig(role.name)` retrieves agent configuration
   - Configuration includes tools, prompt file, display name

4. **System Message Construction**
   - `loadPrompt(promptFile)` reads prompt from `prompts/`
   - `buildSystemMessage(role, prompt, constitution)` wraps in XML tags
   - Includes constitution if available in artifacts

5. **SDK Session Creation**
   - Creates session with systemMessage and tools
   - Tools are available for agent to invoke during execution
   - Agent operates within role-specific context

6. **Agent Execution**
   - Agent has access to custom tools
   - Can invoke `read_constitution`, `read_spec`, `list_artifacts`
   - Operates under role-specific prompt and behaviors

## Agent Roles

| Role | Label | Prompt File | Tools |
|------|-------|-------------|-------|
| **Spec** | role:spec | kickoff-spec.md | read_constitution, list_artifacts |
| **Architect** | role:architect | architecture-design.md | read_constitution, read_spec, list_artifacts |
| **SWE** | role:swe | implementation-swe.md | read_constitution, read_spec, list_artifacts |
| **Deploy** | role:deploy | deployment-ops.md | read_constitution, read_spec, list_artifacts |
| **Security** | role:security | security-review.md | read_constitution, read_spec, list_artifacts |
| **Triage** | role:triage | triage-analysis.md | read_constitution, list_artifacts |

## Testing

### Test Coverage

- **tools.test.ts**: 11 tests for custom tools
- **agent-configs.test.ts**: 11 tests for agent configurations
- **prompt-loader.test.ts**: 8 tests for prompt loading
- **agent-orchestrator.test.ts**: 13 tests for role determination

**Total: 43 tests passing** ✅

### Test Scenarios

1. Tool parameter validation
2. Tool handler execution
3. Agent configuration structure
4. Tool assignments per role
5. Prompt loading from filesystem
6. System message formatting
7. Role detection from labels
8. Autonomy gate validation

## Usage Examples

### Manual Testing

```bash
# Build the service
npm run build

# Run tests
npm test

# Start service (requires GitHub App credentials)
npm start
```

### Triggering an Agent

1. Create GitHub issue
2. Add role label (e.g., `role:spec`)
3. Add autonomy gate label (`agent:go`)
4. Workflow triggers SDK Agent Service
5. Agent executes with role-specific configuration
6. PR created with results

## Benefits

1. **Role-Specific Behavior**: Each agent has tailored prompts and tools
2. **Constitution Awareness**: All agents receive constitution principles
3. **Tool Access**: Agents can read specs, artifacts, and constitution
4. **SDK Native**: Uses official SDK features (systemMessage, tools)
5. **Extensible**: Easy to add new agents and tools
6. **Testable**: Comprehensive test coverage for all components

## Future Enhancements

Potential additions:
- `validate_checklist` tool for artifact contract verification
- `search_codebase` tool for semantic code search
- `create_plan` tool for structured plan generation
- Additional agent roles (reviewer, documenter, etc.)
- Custom agents in SessionConfig (full SDK feature support)

## Files Changed

### New Files
- `src/agents/index.ts`
- `src/agents/types.ts`
- `src/agents/prompt-loader.ts`
- `src/agents/README.md`
- `src/tools/read-constitution.ts`
- `src/tools/read-spec.ts`
- `src/tools/list-artifacts.ts`
- `src/tools/index.ts`
- `tests/agent-configs.test.ts`
- `tests/prompt-loader.test.ts`
- `tests/tools.test.ts`

### Modified Files
- `src/copilot-sdk.d.ts` - Added types for tools and systemMessage
- `src/sdk-client.ts` - Integrated agent configurations
- `package.json` - Added zod dependency

### Build Artifacts
- All source files compiled to `dist/`
- Type definitions generated
- Source maps created

## Acceptance Criteria Status

- [x] All 6 agent roles have SDK-compatible definitions
- [x] System prompts load from existing `prompts/*.md` files
- [x] At least 3 custom tools implemented (3 implemented)
- [x] AgentOrchestrator uses new agent configs
- [x] Tests verify agent selection and tool invocation (43 tests)
- [x] Agents respect constitution principles in output

## Documentation

- Agent persona README in `src/agents/README.md`
- Tool usage examples
- Architecture diagrams
- Test coverage details
- Integration flow documentation
