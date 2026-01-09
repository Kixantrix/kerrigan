# Tasks: Hello API

Each task should be executable and have "done" criteria.

## Milestone 0: Project Setup

- [x] Task: Create project spec.md
  - Done when: spec.md has goal, scope, acceptance criteria, risks
  - Links: specs/projects/hello-api/spec.md

- [x] Task: Create acceptance-tests.md
  - Done when: tests cover all endpoints and edge cases
  - Links: specs/projects/hello-api/acceptance-tests.md

- [x] Task: Create architecture.md
  - Done when: documents components, data flows, tradeoffs
  - Links: specs/projects/hello-api/architecture.md

- [x] Task: Create plan.md
  - Done when: has 4+ milestones from setup to deployment
  - Links: specs/projects/hello-api/plan.md

- [ ] Task: Create tasks.md (this file)
  - Done when: has executable tasks with done criteria for each milestone
  - Links: specs/projects/hello-api/tasks.md

- [ ] Task: Create test-plan.md
  - Done when: defines testing strategy and coverage goals
  - Links: specs/projects/hello-api/test-plan.md

- [ ] Task: Validate spec artifacts
  - Done when: `python tools/validators/check_artifacts.py` passes for hello-api
  - Links: tools/validators/check_artifacts.py

## Milestone 1: Core Implementation

- [ ] Task: Create project structure
  - Done when: examples/hello-api/ exists with all required files
  - Links: architecture.md (project structure section)

- [ ] Task: Set up Python dependencies
  - Done when: requirements.txt exists with Flask and basic dependencies
  - Links: architecture.md (technology stack)

- [ ] Task: Create .gitignore
  - Done when: .gitignore excludes venv/, __pycache__/, *.pyc
  - Links: examples/hello-api/.gitignore

- [ ] Task: Implement config.py
  - Done when: Config class loads PORT and LOG_LEVEL from environment
  - Links: architecture.md (configuration component)

- [ ] Task: Implement validators.py
  - Done when: validate_name() and validate_json_body() work correctly
  - Links: architecture.md (request validation component)

- [ ] Task: Implement handlers.py
  - Done when: health_check(), greet(), echo() functions implemented
  - Links: architecture.md (route handlers component)

- [ ] Task: Implement app.py
  - Done when: Flask app created, routes registered, server can start
  - Links: architecture.md (application entry point)

- [ ] Task: Add logging setup
  - Done when: Requests logged with method, path, status code
  - Links: acceptance-tests.md (logging scenario)

- [ ] Task: Create README.md
  - Done when: README has installation, setup, and usage instructions
  - Links: examples/hello-api/README.md

- [ ] Task: Manual smoke test
  - Done when: All three endpoints work via curl/browser
  - Links: acceptance-tests.md (manual verification checklist)

## Milestone 2: Testing & Quality

- [ ] Task: Set up pytest infrastructure
  - Done when: tests/ directory exists with conftest.py and __init__.py
  - Links: architecture.md (testing component)

- [ ] Task: Create pytest fixtures
  - Done when: conftest.py has app and client fixtures
  - Links: architecture.md (testing component)

- [ ] Task: Write test_health.py
  - Done when: Health endpoint tests pass
  - Links: acceptance-tests.md (health check scenarios)

- [ ] Task: Write test_greet.py
  - Done when: Greeting endpoint tests cover all scenarios
  - Links: acceptance-tests.md (greeting scenarios)

- [ ] Task: Write test_echo.py
  - Done when: Echo endpoint tests cover all scenarios
  - Links: acceptance-tests.md (echo scenarios)

- [ ] Task: Write test_integration.py
  - Done when: Full request/response cycle tests pass
  - Links: test-plan.md

- [ ] Task: Add pytest to requirements
  - Done when: requirements.txt includes pytest and pytest-flask
  - Links: architecture.md (technology stack)

- [ ] Task: Verify test coverage
  - Done when: pytest-cov shows >80% coverage
  - Links: spec.md (acceptance criteria)

- [ ] Task: Add linting configuration
  - Done when: .flake8 or pyproject.toml has linting rules
  - Links: spec.md (quality criteria)

- [ ] Task: Run and fix linter
  - Done when: flake8 or black runs clean
  - Links: spec.md (quality criteria)

- [ ] Task: Update CI workflow
  - Done when: CI runs pytest and linting for hello-api
  - Links: .github/workflows/ci.yml

- [ ] Task: Verify CI passes
  - Done when: All CI checks are green
  - Links: plan.md (milestone requirement)

## Milestone 3: Containerization & Documentation

- [ ] Task: Add gunicorn dependency
  - Done when: requirements.txt includes gunicorn
  - Links: architecture.md (WSGI server)

- [ ] Task: Create Dockerfile
  - Done when: Dockerfile builds python:3.11-slim image with app
  - Links: architecture.md (containerization)

- [ ] Task: Create .dockerignore
  - Done when: .dockerignore excludes venv/, tests/, __pycache__/
  - Links: examples/hello-api/.dockerignore

- [ ] Task: Test Docker build
  - Done when: `docker build -t hello-api .` succeeds
  - Links: acceptance-tests.md (Docker build scenario)

- [ ] Task: Test Docker run
  - Done when: Container starts and /health responds
  - Links: acceptance-tests.md (Docker run scenario)

- [ ] Task: Create runbook.md
  - Done when: runbook has deployment, operation, debugging steps
  - Links: specs/projects/hello-api/runbook.md

- [ ] Task: Create cost-plan.md
  - Done when: cost-plan documents resource usage (minimal for this example)
  - Links: specs/projects/hello-api/cost-plan.md

- [ ] Task: Update README with Docker
  - Done when: README includes Docker build and run instructions
  - Links: examples/hello-api/README.md

- [ ] Task: Manual Docker verification
  - Done when: Full Docker workflow works end-to-end
  - Links: acceptance-tests.md (containerization scenarios)

## Milestone 4: Validation & Polish

- [ ] Task: Run acceptance test checklist
  - Done when: All items in acceptance-tests.md verified manually
  - Links: acceptance-tests.md (manual verification checklist)

- [ ] Task: Run artifact validators
  - Done when: check_artifacts.py passes for hello-api project
  - Links: tools/validators/check_artifacts.py

- [ ] Task: Verify all CI checks
  - Done when: CI is green across all commits
  - Links: plan.md (success criteria)

- [ ] Task: Test Docker image end-to-end
  - Done when: Build, run, and verify all endpoints in container
  - Links: acceptance-tests.md

- [ ] Task: Document friction points
  - Done when: At least 3 workflow improvements documented in handoffs.md
  - Links: playbooks/handoffs.md

- [ ] Task: Update agent prompts
  - Done when: Role prompts updated based on learnings
  - Links: .github/agents/role.*.md

- [ ] Task: Update plan.md with lessons
  - Done when: Kerrigan plan.md updated with Milestone 5 completion
  - Links: specs/projects/kerrigan/plan.md

- [ ] Task: Final documentation review
  - Done when: All docs are accurate and complete
  - Links: All spec artifacts

- [ ] Task: Mark milestone complete
  - Done when: Issue closed, lessons documented
  - Links: GitHub issue
