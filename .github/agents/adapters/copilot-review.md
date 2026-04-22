# Adapter: GitHub Copilot code-review agent

**Runtime:** GitHub (built-in, cloud).
**Invocation:** Automatic on PR open (when repo setting enabled).
**Writes:** PR review comments only.

## Use when

Always on. This is the default Copilot PR review. The `local` profile doesn't invoke it per-task — it runs because the repo setting is on.

## Configuration

Enable in repo settings → Copilot → "Automatic pull request reviews". Required for Phase 2 of v2 rollout.

## How it fits the verification chain

Cloud self-test → CI (unit + integration + smoke) → spec-kit verify chain → **Copilot review (this)** → human scenario check.

The review agent catches:

- Style/readability issues.
- Obvious bugs (null, off-by-one, unused, etc.).
- Missing tests *patterns* (doesn't enforce AC↔test — that's `spec-kit-verify-tasks`).

## Don't rely on it for

- Acceptance-criteria coverage. Use `spec-kit-verify` / `spec-kit-verify-tasks`.
- Security review. Use `spec-kit-security-review` or a dedicated pass.
- Architectural fit. That's a human scenario check.
