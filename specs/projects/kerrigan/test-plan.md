# Test plan: Kerrigan

## Levels

### Unit tests
- **Validators**: test each check in isolation
  - `check_artifacts.py`: test missing files, missing sections, conditional requirements
  - `check_quality_bar.py`: test LOC thresholds, ignore patterns, various file extensions
- **Status schema**: validate status.json parsing and state transitions

### Integration tests
- **CI workflows**: test that validators run on PR and fail/pass correctly
  - Create test branches with intentional artifact violations
  - Verify CI blocks merge appropriately
- **Autonomy gates**: test label-based controls
  - Mock PRs with/without required labels
  - Verify gate enforcement logic

### End-to-end tests
- **Agent workflow**: run full spec → deploy cycle
  - Use example project or create throw-away test project
  - Invoke each agent role in sequence
  - Verify artifacts produced at each step
  - Confirm CI stays green throughout
- **Pause/resume**: test status.json blocking
  - Set project to "blocked" status
  - Verify agents halt work
  - Set to "active" and verify resumption

### Manual tests (human-validated)
- **Playbook usability**: new user follows kickoff.md
- **Agent prompt clarity**: agents produce expected outputs without confusion
- **PR review experience**: humans can review agent PRs in < 15 min

## Tooling

### Python testing
- Framework: `pytest`
- Coverage: aim for >80% on validator logic
- Run in CI: add test job to `.github/workflows/ci.yml`

### GitHub Actions testing
- Use `act` (local GitHub Actions runner) or test on branches
- Document expected CI behaviors in acceptance-tests.md

### Agent testing
- Manual invocation with recorded results
- Playbook for agent testing workflow
- Track success/failure metrics over time

## Risk areas / focus

### High risk: Validator correctness
- **Why**: validators are the enforcement layer; bugs allow broken state
- **Focus**: thorough edge case coverage
  - Empty files, partial sections, malformed markdown
  - Large files with various extensions
  - Projects without runbook/cost-plan (non-deployable)

### Medium risk: Autonomy gate bypass
- **Why**: agents could circumvent controls if label checks are flawed
- **Focus**: test all label combinations
  - Missing labels, wrong labels, override labels
  - Multiple modes, conflicting signals

### Medium risk: Status tracking race conditions
- **Why**: multiple agents might update status.json simultaneously
- **Focus**: document single-writer semantics
  - Recommend status updates only at PR merge, not during work

### Low risk: Playbook clarity
- **Why**: humans can adapt if instructions are unclear
- **Focus**: user testing and iteration based on feedback
