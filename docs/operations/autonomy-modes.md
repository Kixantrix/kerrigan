# Autonomy modes

Kerrigan separates accepted authority from dispatch transport. Follow [session operations](../../playbooks/session-operations.md) for primary app-session dispatch, ownership, and stop conditions. Profile, host, and runtime permissions are separate; this guide grants no new authority.

## Execution gate

Direct app sessions start from an accepted outcome and actionable briefing/task context; no issue or label is required to dispatch an explicit executor on a capability-appropriate host.

The optional issue adapter retains the existing issue scripts and `@copilot` assignment flow. `agent:go` annotates readiness; `agent:wait` annotates intentional waiting. Neither label starts or stops an app session, and labels alone do not assign an issue agent. Use explicit assignment for issue dispatch, and the owning runtime's supported stop mechanism for active work. Confirm process/resource release rather than treating label changes or idle status as proof of stopping.

Repository-specific issue/label merge gates still apply where configured. Satisfy them through the authorized adapter or report the blocker; never infer an override from session-first dispatch. Permission, budget, and human-approved exception rules are unchanged.

## Merge gate (review response flow)

Required checks and review-thread resolution remain gates where configured. The coordinator inspects actual current-head review/check evidence and routes fixes to the existing implementation owner on the same branch, by session message or the optional issue adapter. A configured reviewer is not completed review evidence; only an authorized lifecycle owner advances merge.

See [`.github/agents/kerrigan.md` — "Review response flow"](../../.github/agents/kerrigan.md#review-response-flow).
