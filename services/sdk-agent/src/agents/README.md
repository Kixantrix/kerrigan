# Kerrigan Agent Personas

This directory contains SDK-compatible agent configurations with role-specific tools and system prompts.

## Overview

Each agent persona is defined with:
- **Name**: Unique identifier (e.g., `kerrigan-spec`)
- **Display Name**: Human-readable name
- **Description**: Agent's purpose and responsibilities
- **Prompt File**: Markdown file from `prompts/` directory
- **Label**: GitHub label for agent selection (e.g., `role:spec`)
- **Tools**: Array of custom tools the agent can invoke

## Available Agents

### 1. Spec Agent (`kerrigan-spec`)
**Label:** `role:spec`  
**Prompt:** `kickoff-spec.md`  
**Tools:** `read_constitution`, `list_artifacts`

Creates project specifications following Kerrigan conventions. Defines acceptance criteria and validates against constitution principles.

### 2. Architect Agent (`kerrigan-architect`)
**Label:** `role:architect`  
**Prompt:** `architecture-design.md`  
**Tools:** `read_constitution`, `read_spec`, `list_artifacts`

Designs systems following architecture patterns. Creates `plan.md` with implementation tasks and references existing architecture docs.

### 3. SWE Agent (`kerrigan-swe`)
**Label:** `role:swe`  
**Prompt:** `implementation-swe.md`  
**Tools:** `read_constitution`, `read_spec`, `list_artifacts`

Implements code with tests following test-first development. Links tests to source files and follows constitution principles.

### 4. Deploy Agent (`kerrigan-deploy`)
**Label:** `role:deploy`  
**Prompt:** `deployment-ops.md`  
**Tools:** `read_constitution`, `read_spec`, `list_artifacts`

Creates runbooks and cost estimates. Documents operational procedures and considers infrastructure requirements.

### 5. Security Agent (`kerrigan-security`)
**Label:** `role:security`  
**Prompt:** `security-review.md`  
**Tools:** `read_constitution`, `read_spec`, `list_artifacts`

Reviews for security vulnerabilities. Checks authentication/authorization and validates input handling.

### 6. Triage Agent (`kerrigan-triage`)
**Label:** `role:triage`  
**Prompt:** `triage-analysis.md`  
**Tools:** `read_constitution`, `list_artifacts`

Categorizes and prioritizes issues. Suggests appropriate roles and identifies blockers.

## Custom Tools

### `read_constitution`
Reads Kerrigan constitution principles from `specs/constitution.md`.

**Parameters:** None

### `read_spec`
Reads project specification from `specs/projects/{project}/spec.md`.

**Parameters:**
- `project` (optional): Project name/directory

### `list_artifacts`
Lists existing project artifacts including specs, plans, architecture docs, ADRs, and runbooks.

**Parameters:**
- `project` (optional): Project name to list artifacts for

## Usage

Agents are automatically selected based on GitHub issue labels. The SDK client loads the appropriate agent configuration and creates a session with:
- System message containing agent prompt and constitution
- Custom tools specific to the agent role
- Proper context for the agent's responsibilities

```typescript
import { getAgentConfig } from './agents';

// Get agent configuration by role
const agentConfig = getAgentConfig('spec');

// Create SDK session with agent configuration
const session = await client.createSession({
  model: 'gpt-4o',
  systemMessage: {
    content: buildSystemMessage(
      'spec',
      loadPrompt('kickoff-spec.md'),
      constitutionContent
    ),
  },
  tools: agentConfig.tools,
});
```

## Adding New Agents

To add a new agent persona:

1. Create prompt file in `prompts/` directory
2. Add agent configuration to `KERRIGAN_AGENTS` in `index.ts`
3. Assign appropriate tools from `src/tools/`
4. Add corresponding label mapping in `agent-orchestrator.ts`
5. Add tests in `tests/agent-configs.test.ts`

## Adding New Tools

To add a new custom tool:

1. Create tool file in `src/tools/`
2. Define tool with zod schema for parameters
3. Implement handler function
4. Export from `src/tools/index.ts`
5. Assign to relevant agent configurations
6. Add tests in `tests/tools.test.ts`

Example tool structure:

```typescript
import { z } from 'zod';

export const myTool = {
  name: 'my_tool',
  description: 'Description of what the tool does',
  parameters: z.object({
    param1: z.string().optional(),
  }),
  handler: async (params: { param1?: string }): Promise<string> => {
    // Tool implementation
    return 'result';
  },
};
```
