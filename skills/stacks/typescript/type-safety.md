---
title: TypeScript Type Safety Patterns
version: 1.0.0
source: Community (adapted)
source_url: https://www.typescriptlang.org/docs/handbook/
quality_tier: 2
last_reviewed: 2026-01-23
last_updated: 2026-01-23
reviewed_by: kerrigan-swe-team
license: MIT
tags: [typescript, types, safety, patterns]
applies_to: [typescript, javascript]
---

# TypeScript Type Safety Patterns

*Adapted from TypeScript handbook and community best practices for Kerrigan projects.*

This skill covers type safety patterns for TypeScript projects, ensuring robust and maintainable code.

## When to Apply

Reference this skill when:
- Starting a TypeScript project
- Refactoring JavaScript to TypeScript
- Designing type-safe APIs and interfaces
- Debugging type errors
- Ensuring code quality through types

## Key Patterns

### Pattern 1: Strict Mode Configuration

Always enable strict mode in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### Pattern 2: Type Guards for Runtime Safety

```typescript
// Type guard function
function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj
  )
}

// Usage
function processData(data: unknown) {
  if (isUser(data)) {
    // TypeScript knows data is User here
    console.log(data.name)
  }
}
```

### Pattern 3: Discriminated Unions for State Management

```typescript
type LoadingState = { status: 'loading' }
type SuccessState = { status: 'success'; data: User }
type ErrorState = { status: 'error'; error: string }

type State = LoadingState | SuccessState | ErrorState

function renderState(state: State) {
  switch (state.status) {
    case 'loading':
      return 'Loading...'
    case 'success':
      return `User: ${state.data.name}`
    case 'error':
      return `Error: ${state.error}`
  }
}
```

## References

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [Kerrigan Quality Bar](../../meta/quality-bar.md)

## Updates

**v1.0.0 (2026-01-23):** Initial version adapted from TypeScript handbook for Kerrigan projects
