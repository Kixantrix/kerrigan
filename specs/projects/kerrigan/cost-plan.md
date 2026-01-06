# Cost plan: Kerrigan

## Cost drivers

### Agent API usage
- **Primary cost**: LLM API calls (e.g., OpenAI, Anthropic, GitHub Copilot)
- **Variables**:
  - Number of agents invoked per project
  - Size of context (constitution, specs, artifacts)
  - Number of iterations (revisions, PR updates)
  - Model choice (GPT-4, Claude Sonnet, etc.)

### GitHub Actions minutes
- **Secondary cost**: CI runs on each PR
- **Variables**:
  - Number of PRs per project
  - Complexity of validators (runtime)
- **Estimate**: negligible (< 100 compute minutes/month for typical project)

### Developer time
- **Human review**: 5-15 min per PR
- **Autonomy tuning**: 1-2 hours per project (setup labels, calibrate modes)
- **Swarm steering**: ongoing, varies by project complexity

## Baseline estimate

### Small project (< 10 PRs)
- **Agent API**: $5-20 (depends on model and iterations)
- **GitHub Actions**: free tier sufficient
- **Human time**: 2-4 hours total

### Medium project (10-50 PRs)
- **Agent API**: $50-200
- **GitHub Actions**: free tier sufficient
- **Human time**: 10-20 hours total

### Large project (50+ PRs)
- **Agent API**: $200-1000+
- **GitHub Actions**: may exceed free tier ($0.008/min after 2000 min)
- **Human time**: 40+ hours total

**Note**: agent API costs vary widely by provider and model tier. These are rough estimates.

## Guardrails (budgets/alerts/tags)

### Agent API cost control
- **Budget**: set monthly spend limit in LLM provider dashboard
- **Alerts**: configure usage notifications at 50%, 75%, 90% thresholds
- **Rate limiting**: limit agent invocations per day (manual or via script)
- **Model downgrade**: use cheaper models for non-critical roles (e.g., testing agent)

### GitHub Actions cost control
- **Monitor**: check Actions usage in repo Insights → Actions
- **Optimize validators**: keep Python scripts fast (< 10 sec runtime)
- **Cache dependencies**: if validators grow, cache Python environment

### Human time optimization
- **Small PRs**: enforce via quality bar (faster to review)
- **Clear artifacts**: reduce back-and-forth via strict contracts
- **Autonomy modes**: batch work in sprints to minimize context switching

## Scale assumptions

### Assumptions
- Average PR review time: 10 minutes
- Average agent iterations per PR: 2-3
- CI runtime per PR: < 1 minute
- Projects run for 1-3 months before completion

### Scaling strategies
- **Parallel projects**: multiple projects can share same Kerrigan repo
- **Cost per project**: isolate agent API keys per project for tracking
- **Cost attribution**: tag agent invocations with project name in logs
- **Optimization over time**: agents learn patterns, reduce iterations

### When costs exceed baseline
- **Review autonomy mode**: switch to on-demand if too many PRs
- **Optimize agent prompts**: reduce unnecessary context
- **Human intervention**: directly edit artifacts instead of agent iteration
- **Model selection**: use cheaper models for routine tasks
