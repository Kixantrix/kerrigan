# Architecture: Spec Agent

## Overview

The Spec Agent operates as a requirements engineering specialist within the Kerrigan agent swarm. It transforms human-provided project ideas into structured, measurable specifications that serve as the foundation for all downstream work. The agent bridges the gap between stakeholder intent and technical implementation by producing artifact-driven documentation that multiple agents and humans can reference throughout the project lifecycle.

The agent's architecture is intentionally lightweight and document-focused, with no complex state management or external dependencies beyond reading repository context and writing markdown artifacts.

## Components & interfaces

### Input Sources
- **Human project brief**: Initial description of project idea, problem statement, or feature request
- **status.json**: Project workflow status file (if exists) - agent must check before proceeding
- **constitution.md**: Governing principles that specs must align with
- **artifact contracts**: Required section headings and structure definitions
- **Existing project artifacts**: When updating specs, reads current spec.md, architecture.md, decisions.md

### Core Processing
- **Requirement Analyzer**: Extracts key elements from project brief
  - Identifies goals, users, constraints, and success criteria
  - Distinguishes functional vs. non-functional requirements
  - Detects ambiguity or missing information
- **Measurability Validator**: Ensures acceptance criteria are concrete
  - Flags subjective terms ("good", "fast", "reliable")
  - Transforms vague criteria into measurable thresholds
  - Validates criteria can be tested
- **Scope Boundary Enforcer**: Separates "what" from "how"
  - Identifies and removes implementation details
  - Marks architectural decisions for Architect Agent
  - Ensures spec stays at appropriate abstraction level
- **Artifact Formatter**: Produces correctly structured markdown
  - Enforces exact section heading names (case-sensitive)
  - Validates required sections are present
  - Generates Given/When/Then test scenarios

### Output Artifacts
- **spec.md**: Primary specification document
  - Sections: Goal, Scope, Non-goals, Users & scenarios, Constraints, Acceptance criteria, Risks & mitigations, Success metrics
- **acceptance-tests.md**: Human-readable test scenarios
  - Given/When/Then format or checklist style
  - Covers happy path, edge cases, and failure modes
- **decisions.md**: Architectural decision records (ADR-lite)
  - Documents tradeoffs when multiple approaches are viable at spec level
  - Records why certain items are in-scope vs. non-goals

### Validation Interface
- Agent output must pass artifact validators that check:
  - Required sections present
  - Section headings match exactly (case-sensitive)
  - File exists at expected path
  - Links between artifacts are valid

## Data flow (conceptual)

```
[Human Project Idea]
        ↓
[Status Check] → (if blocked/on-hold) → [Stop & Report]
        ↓
[Requirement Analysis]
        ↓
[Measurability Validation] ← [Constitution Principles]
        ↓                            ↓
[Scope Boundaries]              [Artifact Contract]
        ↓                            ↓
[Generate spec.md] ──────────────────┘
        ↓
[Generate acceptance-tests.md]
        ↓
[Optional: Generate decisions.md]
        ↓
[Artifacts Written to Repo]
        ↓
[Available for Architect Agent]
```

## Tradeoffs

### Document-First vs. Interactive Clarification
**Decision**: Produce best-effort spec from available information, mark ambiguities explicitly
- **Pro**: Enables async workflow; spec serves as basis for clarification discussions
- **Con**: May require iteration if initial brief is insufficient
- **Mitigation**: Include questions and assumptions in spec; encourage human review before architecture phase

### Strict Structure vs. Flexibility
**Decision**: Enforce exact section headings and required sections (artifact contract)
- **Pro**: Enables automated validation; ensures consistency across projects; agents know where to find information
- **Con**: May feel rigid for very small projects; some sections might be brief
- **Mitigation**: Allow sections to be brief but present; provide templates and examples

### Prescriptive Criteria vs. User Freedom
**Decision**: Require measurable acceptance criteria but don't dictate specific metrics
- **Pro**: Balances clarity with flexibility; adapts to different project types
- **Con**: Still requires judgment on what "measurable" means
- **Mitigation**: Provide examples of good/bad criteria in agent prompt; offer patterns

### Spec Updates vs. Immutability
**Decision**: Specs can be updated but maintain history via git
- **Pro**: Accommodates legitimate scope changes and clarifications
- **Con**: Risk of spec drift from implemented system
- **Mitigation**: Require spec updates to be deliberate (not casual); link to decisions.md when changing scope

## Security & privacy notes

### Information Handling
- Spec Agent processes project requirements which may contain:
  - **Sensitive business logic**: Should be documented but not shared externally
  - **Compliance requirements**: Must be captured in acceptance criteria (GDPR, HIPAA, etc.)
  - **Security requirements**: Should be explicit in spec, not assumed

### Secret Management
- Agent must NOT document actual secrets (API keys, passwords, credentials)
- May document that secrets are required (e.g., "Authentication via OAuth2")
- Should reference secret management approach at high level if it's a requirement

### Access Control
- Spec artifacts are committed to repository and follow repo access controls
- Consider sensitivity of requirements when writing specs for private vs. public repos
- Mark particularly sensitive requirements if necessary

### Input Validation
- Agent should validate that project brief doesn't contain inadvertent secret exposure
- Flag if brief contains patterns that look like credentials or API keys
- Warn if non-goals or constraints reveal security-sensitive architectural details

### Alignment with Security Agent
- Spec Agent should identify security-sensitive requirements
- Security Agent later reviews architecture for security considerations
- Handoff: Spec clearly states security acceptance criteria → Security Agent validates architecture meets them
