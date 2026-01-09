# Plan: Hello API

Each milestone must end with green CI.

## Milestone 0: Project Setup
**Status**: 🔄 In Progress

- [x] Create project spec.md with requirements
- [x] Create acceptance-tests.md with test scenarios
- [x] Create architecture.md with technical design
- [x] Create plan.md (this file)
- [ ] Create tasks.md with executable tasks
- [ ] Create test-plan.md with testing strategy
- [ ] Validate artifacts with check_artifacts.py

**Deliverable**: Complete specification artifacts

**Dependencies**: None

**Rollback**: Delete specs/projects/hello-api/ folder

## Milestone 1: Core Implementation
**Status**: ⏳ Pending

**Goal**: Implement working API with all three endpoints

- [ ] Set up Python project structure
- [ ] Implement configuration management
- [ ] Implement health check endpoint
- [ ] Implement greet endpoint with validation
- [ ] Implement echo endpoint with JSON handling
- [ ] Add error handling for all endpoints
- [ ] Add basic logging
- [ ] Create README with setup instructions
- [ ] All endpoints working and manually tested

**Deliverable**: Working API service that can be run locally

**Dependencies**: Milestone 0 (specifications complete)

**Rollback**: Delete examples/hello-api/ folder

**Tasks**: See Milestone 1 section in tasks.md

## Milestone 2: Testing & Quality
**Status**: ⏳ Pending

**Goal**: Add comprehensive test coverage and CI integration

- [ ] Set up pytest and testing infrastructure
- [ ] Write unit tests for validators
- [ ] Write unit tests for handlers
- [ ] Write integration tests for endpoints
- [ ] Add test fixtures and utilities
- [ ] Achieve >80% code coverage
- [ ] Add linting/formatting (flake8, black)
- [ ] Update CI workflow to run tests
- [ ] All tests passing, CI green

**Deliverable**: Fully tested API with CI validation

**Dependencies**: Milestone 1 (core implementation)

**Rollback**: Remove test files; keep working implementation

**Tasks**: See Milestone 2 section in tasks.md

## Milestone 3: Containerization & Documentation
**Status**: ⏳ Pending

**Goal**: Make API deployable via Docker with complete documentation

- [ ] Create Dockerfile
- [ ] Create .dockerignore
- [ ] Test Docker build
- [ ] Test running container
- [ ] Add gunicorn for production WSGI server
- [ ] Create runbook.md with deployment steps
- [ ] Create cost-plan.md (minimal for this example)
- [ ] Update README with Docker instructions
- [ ] Test full deployment workflow

**Deliverable**: Containerized API ready for deployment

**Dependencies**: Milestone 2 (testing complete)

**Rollback**: Remove Docker files; keep working tested implementation

**Tasks**: See Milestone 3 section in tasks.md

## Milestone 4: Validation & Polish
**Status**: ⏳ Pending

**Goal**: Final validation and documentation polish

- [ ] Manual verification of all acceptance criteria
- [ ] Run validators on all spec artifacts
- [ ] Verify CI passes on all commits
- [ ] Test Docker image end-to-end
- [ ] Update project documentation based on learnings
- [ ] Document friction points in handoffs.md
- [ ] Mark hello-api as complete example

**Deliverable**: Production-ready example meeting all acceptance criteria

**Dependencies**: Milestone 3 (containerization complete)

**Rollback**: Not applicable (polish only)

**Tasks**: See Milestone 4 section in tasks.md

## Success Criteria

- ✅ All acceptance criteria from spec.md met
- ✅ CI passes on all commits throughout implementation
- ✅ Test coverage >80%
- ✅ All spec artifacts complete and validated
- ✅ Docker image builds and runs successfully
- ✅ Manual verification checklist complete
- ✅ Example serves as reference for future projects

## Risk Management

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| Scope creep | Medium | Medium | Stick to spec; use acceptance tests as boundary | Active |
| Test flakiness | Low | Low | Use pytest fixtures; avoid timing dependencies | Monitor |
| Docker build issues | Low | Medium | Use stable base image; pin dependencies | Monitor |
| CI failures | Low | High | Test locally first; keep incremental commits | Monitor |

## Timeline Estimate

- Milestone 0: 1-2 hours (specifications) ✅
- Milestone 1: 2-3 hours (implementation)
- Milestone 2: 2-3 hours (testing)
- Milestone 3: 1-2 hours (containerization)
- Milestone 4: 1 hour (validation)

**Total**: ~7-11 hours of focused work

## Notes

- Keep commits small and focused
- Run validators frequently
- Test locally before pushing
- Document any deviations from plan
- Update this plan if scope changes
