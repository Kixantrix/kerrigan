# Kerrigan Examples

Example projects demonstrating Kerrigan workflows and patterns.

## Available Examples

### Single-Repository Examples

#### [hello-api](hello-api/)
A simple Python Flask REST API demonstrating single-repository best practices.

**Purpose**: Learn basic Kerrigan workflow with a simple service  
**Tech Stack**: Python, Flask, Docker  
**Time to Complete**: 5 minutes  
**Best For**: First-time users, single service projects

**Key Features**:
- Complete artifact set (spec, architecture, runbook, etc.)
- Health check, greeting, and echo endpoints
- Comprehensive test coverage
- CI/CD ready

#### [hello-cli](hello-cli/)
A command-line tool example.

**Purpose**: Demonstrate CLI application patterns  
**Best For**: Command-line tool development

#### [hello-swarm](hello-swarm/)
Minimal example demonstrating artifact flow.

**Purpose**: Smallest possible example of Kerrigan artifacts  
**Best For**: Understanding artifact contracts

#### [task-tracker](task-tracker/)
Task management example with multiple features.

**Purpose**: Demonstrate feature-rich application  
**Best For**: Complex single-repo projects

### Multi-Repository Example ⭐

#### [hello-multiapp](MULTI-REPO-WALKTHROUGH.md) (NEW!)
A complete three-repository system demonstrating multi-repo coordination.

**Purpose**: Learn how to coordinate work across multiple repositories  
**Time to Complete**: 10 minutes  
**Best For**: Teams with microservices or multi-repo architectures

**Repositories**:
1. **[hello-multiapp-api](hello-multiapp-api/)** - Python FastAPI backend
2. **[hello-multiapp-frontend](hello-multiapp-frontend/)** - HTML/JS web interface
3. **[hello-multiapp-infra](hello-multiapp-infra/)** - Docker Compose orchestration

**Key Features**:
- Complete artifact set in each repo with cross-repo references
- Task dependencies between repos
- Coordinated deployment via Docker Compose
- Three demonstration scenarios:
  1. **Kickoff**: Spec agent initializes all repos
  2. **Implementation**: SWE agents coordinate changes
  3. **Deployment**: Ops agent deploys using all runbooks

**Quick Start**:
```bash
cd examples/hello-multiapp-infra
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

**What You'll Learn**:
- How to structure multi-repo projects
- Cross-repo dependency management
- Artifact-driven coordination
- Multi-service deployment patterns
- Cost allocation across repos

📚 **[Read the Complete Walkthrough](MULTI-REPO-WALKTHROUGH.md)**

## Learning Path

### For New Users
1. Start with **hello-api** - Learn single-repo basics
2. Try **hello-swarm** - Understand minimal artifacts
3. Explore **hello-multiapp** - Learn multi-repo coordination

### For Teams Adopting Kerrigan
1. **Single service**: Use hello-api as a template
2. **Multiple services**: Study hello-multiapp pattern
3. **Complex projects**: Adapt task-tracker patterns

### For Agent Developers
1. Study artifact contracts in hello-swarm
2. Review cross-repo references in hello-multiapp
3. Understand coordination patterns in multi-repo example

## Comparison Matrix

| Example | Repos | Services | Tech Stack | Complexity | Time |
|---------|-------|----------|------------|------------|------|
| hello-api | 1 | 1 | Python/Flask | ⭐ Simple | 5 min |
| hello-cli | 1 | 1 | Python | ⭐ Simple | 5 min |
| hello-swarm | 1 | 0 | None | ⭐ Minimal | 2 min |
| task-tracker | 1 | 1 | Multiple | ⭐⭐⭐ Complex | 15 min |
| **hello-multiapp** | **3** | **2** | **Python/JS/Docker** | **⭐⭐ Moderate** | **10 min** |

## Quick Reference

### Single-Repo Projects
Use when:
- ✅ Single team owns entire codebase
- ✅ All components deployed together
- ✅ Shared deployment lifecycle
- ✅ Simple dependencies

Examples: hello-api, hello-cli, task-tracker

### Multi-Repo Projects
Use when:
- ✅ Different teams own different services
- ✅ Services scale independently
- ✅ Different deployment schedules
- ✅ Clear service boundaries

Example: **hello-multiapp** ⭐

## Documentation Structure

Each example includes:

### Single-Repo Structure
```
example-name/
├── README.md              # Overview and quick start
├── [source files]         # Application code
└── [optional specs/]      # Kerrigan artifacts
```

### Multi-Repo Structure (hello-multiapp)
```
hello-multiapp-api/
├── README.md
├── main.py
└── specs/
    ├── spec.md            # With repositories array
    ├── tasks.md           # With cross-repo dependencies
    ├── architecture.md    # With integration points
    ├── runbook.md         # With deployment coordination
    └── cost-plan.md       # With cost allocation

hello-multiapp-frontend/
├── README.md
├── index.html
└── specs/                 # Same structure

hello-multiapp-infra/
├── README.md
├── docker-compose.yml
└── specs/                 # Same structure

MULTI-REPO-WALKTHROUGH.md  # Complete guide
```

## Common Patterns

### Pattern 1: Health Checks
All examples include health check endpoints for monitoring.

**See**: hello-api (`/health`), hello-multiapp-api (`/health`)

### Pattern 2: Docker Containerization
Most examples include Dockerfiles for deployment.

**See**: hello-api, hello-multiapp-api, hello-multiapp-frontend

### Pattern 3: Complete Artifacts
Examples demonstrate the full Kerrigan artifact set.

**See**: hello-api (single-repo), hello-multiapp-* (multi-repo)

### Pattern 4: Cross-Repo References
Multi-repo examples show how repos coordinate.

**See**: hello-multiapp-* specs folders

## Testing Examples

### Test hello-api
```bash
cd hello-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
curl http://localhost:5000/health
```

### Test hello-multiapp
```bash
cd hello-multiapp-infra
docker-compose up --build
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

## Contributing

To add a new example:

1. Create a directory in `examples/`
2. Include a comprehensive README.md
3. For multi-repo: Add cross-repo references in specs/
4. Update this README with your example
5. Add to the comparison matrix

## Related Documentation

- [Kerrigan README](../README.md) - Main project documentation
- [Artifact Contracts](../specs/kerrigan/020-artifact-contracts.md) - Artifact specifications
- [Milestone 7 Spec](../specs/projects/kerrigan/milestone-7-spec.md) - Multi-repo features
- [Multi-Repo Walkthrough](MULTI-REPO-WALKTHROUGH.md) - Complete multi-repo guide

## Need Help?

- **New to Kerrigan?** Start with hello-api
- **Need multi-repo?** Read [MULTI-REPO-WALKTHROUGH.md](MULTI-REPO-WALKTHROUGH.md)
- **Have questions?** Check the main [README](../README.md)
- **Want to contribute?** Add a new example following the patterns above

## License

All examples are MIT licensed (see root LICENSE file).
