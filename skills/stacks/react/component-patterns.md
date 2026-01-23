---
title: React Component Patterns
version: 1.0.0
source: Community (adapted)
source_url: https://react.dev/learn
quality_tier: 2
last_reviewed: 2026-01-23
last_updated: 2026-01-23
reviewed_by: kerrigan-swe-team
license: MIT
tags: [react, components, hooks, patterns]
applies_to: [react, typescript, javascript]
---

# React Component Patterns

*Adapted from React documentation and community best practices for Kerrigan projects.*

This skill covers component patterns for React projects, focusing on maintainable and performant code.

## When to Apply

Reference this skill when:
- Building React components
- Refactoring existing React code
- Optimizing component performance
- Managing component state
- Designing component APIs

## Key Patterns

### Pattern 1: Functional Components with Hooks

Prefer functional components over class components:
```tsx
// ✅ Good: Functional component with hooks
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    fetchUser(userId).then(user => {
      setUser(user)
      setLoading(false)
    })
  }, [userId])
  
  if (loading) return <div>Loading...</div>
  if (!user) return <div>User not found</div>
  
  return <div>{user.name}</div>
}
```

### Pattern 2: Custom Hooks for Reusable Logic

Extract common patterns into custom hooks:
```tsx
// Custom hook
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  
  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [userId])
  
  return { user, loading, error }
}

// Usage
function UserProfile({ userId }: { userId: string }) {
  const { user, loading, error } = useUser(userId)
  
  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>
  if (!user) return <div>User not found</div>
  
  return <div>{user.name}</div>
}
```

### Pattern 3: Prop Types with TypeScript

Define clear prop interfaces:
```tsx
interface ButtonProps {
  children: React.ReactNode
  onClick: () => void
  variant?: 'primary' | 'secondary'
  disabled?: boolean
}

function Button({ 
  children, 
  onClick, 
  variant = 'primary',
  disabled = false 
}: ButtonProps) {
  return (
    <button 
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  )
}
```

## References

- [React Documentation](https://react.dev/)
- [Kerrigan Quality Bar](../../meta/quality-bar.md)

## Updates

**v1.0.0 (2026-01-23):** Initial version adapted from React documentation for Kerrigan projects
