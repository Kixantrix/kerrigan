# Changelog

All notable changes to Kerrigan will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-21

### 🎉 Initial Release

Kerrigan is a repo template for defining and evolving a **swarm of agents** that completes software projects the way you want them completed—without you having to be "the glue".

### Core Features

#### Agent System
- **11 specialized agent roles**: spec, architect, swe, testing, deployment, security, debugging, design, triage, and kerrigan (meta-agent)
- **Agent signature system**: Cryptographic verification that agents are using their assigned prompts
- **Agent feedback mechanism**: Continuous improvement through structured feedback collection

#### Artifact Contracts
- **9 required artifacts** per project: spec.md, acceptance-tests.md, architecture.md, plan.md, tasks.md, test-plan.md, runbook.md, cost-plan.md, status.json
- **Validators** enforce artifact existence and structure in CI
- **Multi-repository support** with cross-repo coordination patterns

#### Autonomy Control
- **Three autonomy modes**: on-demand (agent:go), sprint (agent:sprint), override (autonomy:override)
- **Label-based gates** prevent unauthorized agent work
- **Status tracking** via status.json for pause/resume control

#### Quality Enforcement
- **Quality bar**: Maximum 800 LOC per file (with allow:large-file override)
- **CI validators**: check_artifacts.py, check_quality_bar.py, check_pr_documentation.py
- **Agent spec compliance**: Workflow validates agents use correct prompts

#### Workflows & Automation
- **CI workflow**: Runs validators and tests on every PR
- **Agent Gates**: Enforces autonomy modes via label checking
- **Auto-assign**: Automatically assigns reviewers and issues to Copilot
- **Daily self-improvement**: Analyzes feedback and generates improvement reports

#### Documentation
- **Constitution**: 8 non-negotiable principles for quality-first development
- **11 playbooks**: kickoff, handoffs, PR review, autonomy modes, triage, and more
- **Setup guide**: Step-by-step walkthrough for new repositories
- **Examples**: Single-repo and multi-repo project templates

### Technical Details

#### Supported Environments
- **CI**: Ubuntu (GitHub Actions)
- **Local development**: Windows (PowerShell 5.1+), macOS, Linux
- **Python**: 3.8+ for validators

#### Cross-Platform Compatibility
- All tests pass on both Ubuntu and Windows
- PowerShell scripts compatible with 5.1 and 7+
- UTF-8 encoding specified throughout for international character support

### Getting Started

1. Use this repo as a template
2. Create required GitHub labels (agent:go, agent:sprint, autonomy:override, role:*)
3. Create an issue with your project idea
4. Add agent:go label and assign to Copilot
5. Let agents build: Spec → Architecture → Implementation → Testing → Deploy

See [docs/setup.md](docs/setup.md) for detailed instructions.

---

## [Unreleased]

### Added
- **Version tracking system**: `kerrigan-version.json` manifest tracks installed version and component versions
- **Upgrade automation**: `tools/upgrade-kerrigan.ps1` PowerShell script for selective component upgrades
- **Upgrade playbook**: Comprehensive guide for upgrading satellite installations (`playbooks/upgrade-satellite.md`)

### Features

#### Version Manifest (`kerrigan-version.json`)
- Track main version and individual component versions (workflows, prompts, validators, skills, playbooks, tools)
- Record installation date and last update timestamp
- Link to upstream repository for easy reference

#### Upgrade Script (`tools/upgrade-kerrigan.ps1`)
- Selective component upgrades (choose which components to update)
- Dry-run mode to preview changes without applying
- Show-diff mode for detailed change visualization
- Automatic version manifest updates
- Conflict detection and clean working directory validation
- Preserves project-specific customizations

#### Upgrade Process
- Automated fetching from upstream Kerrigan repository
- Component-based upgrade strategy (workflows, prompts, validators, skills, playbooks, tools)
- Multiple upgrade methods: automated script, manual cherry-pick, template branch merge
- Post-upgrade validation checklist
- Rollback procedures documented

### Documentation
- Added comprehensive upgrade playbook with examples and troubleshooting
- Component-specific upgrade notes for workflows, prompts, and validators
- Breaking change handling guide
- Conflict resolution strategies

### Planned
- See open issues for upcoming features

[1.0.0]: https://github.com/Kixantrix/kerrigan/releases/tag/v1.0.0
[Unreleased]: https://github.com/Kixantrix/kerrigan/compare/v1.0.0...HEAD
