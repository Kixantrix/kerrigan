# Toolchain and ops (stack-agnostic)

## GitHub workflow
- PRs are the unit of change.
- CI enforces artifact completeness and baseline quality heuristics.
- Autonomy gates optionally control when agents may open PRs.

## Secrets
- Use GitHub Secrets or environment-specific secret stores.
- Never commit .env files or credentials.

## Azure (optional)
This repo does not mandate Azure services. If a project deploys to Azure:
- Document environment strategy in `runbook.md`
- Include cost guardrails in `cost-plan.md`
- Use tagging and budgets/alerts where appropriate
