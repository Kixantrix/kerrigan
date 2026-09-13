"""Static instruction-contract checks, not runtime agent-picker assertions."""

from pathlib import Path
import re

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
PROFILES = ROOT / ".github" / "agents"


@pytest.mark.parametrize(
    "context,assignment,role",
    [
        ("Local human-facing", "None", "kerrigan"),
        ("Known cloud execution", "None", "cloud"),
        ("Local worktree", "Delegated worker", "cloud"),
        ("Known cloud execution", "Delegated worker", "cloud"),
        ("Local human-facing", "Selected `cloud`", "cloud"),
        ("Known cloud execution", "Selected `cloud`", "cloud"),
        ("Local human-facing", "Selected `kerrigan`", "kerrigan"),
        ("Known cloud execution", "Selected `kerrigan`", "kerrigan"),
    ],
)
def test_canonical_startup_examples(context, assignment, role):
    assert f"| {context} | {assignment} | `{role}` |" in AGENTS


def test_canonical_precedence_and_runtime_boundary():
    policy = AGENTS.split("### Startup role policy\n", 1)[1].split(
        "### Outcome ownership\n", 1
    )[0]
    rules = [
        "1. **Explicit assignment wins on either host.**",
        "2. **Known cloud execution defaults to `cloud`.**",
        "3. **Local human-facing sessions default to `kerrigan`.**",
        "4. **Unknown context is not proof of either host.**",
    ]
    positions = [policy.index(rule) for rule in rules]
    assert positions == sorted(positions)
    assert "If explicit instructions conflict" in policy
    assert "route the conflict with evidence to the coordinator" in policy
    assert "not a setting that changes the runtime's agent picker" in policy
    assert "only claim the latter with runtime evidence" in policy
    assert "do not select a model, persist UI state, or change tool permissions" in policy


@pytest.mark.parametrize(
    "path",
    [
        ".github/copilot-instructions.md",
        "CLAUDE.md",
        ".github/agents/README.md",
        ".github/agents/cloud.md",
        ".github/agents/kerrigan.md",
        "README.md",
    ],
)
def test_startup_surfaces_reference_canonical_policy(path):
    text = ROOT.joinpath(*path.split("/")).read_text(encoding="utf-8")
    assert "AGENTS.md#startup-role-policy" in text
    assert "Unless explicitly invoked as the `kerrigan` custom agent" not in text
    assert "defines agents by **location**, not role" not in text


def test_conductor_owns_routine_follow_through_without_expanding_authority():
    text = (PROFILES / "kerrigan.md").read_text(encoding="utf-8")
    assert "A plan or a dispatch is progress, not completion." in text
    assert "**Own routine child decisions.**" in text
    assert "Read a child's pending plan or blocker before responding." in text
    assert "through supported runtime tools" in text
    assert "evidence" in text and "options" in text
    assert "direction, risk, authority, or significant unapproved cost" in text
    assert "does not authorize new permissions, secrets, destructive actions" in text
    assert "Do not exceed the budget" in text
    assert "do not stop at a plan or dispatch" in text


def test_executor_routes_blocks_and_keeps_cohesive_slice():
    text = (PROFILES / "cloud.md").read_text(encoding="utf-8")
    assert "including a local worktree" in text
    assert "Send the block to the coordinator" in text
    assert "attempted fixes, options, and recommendation" in text
    assert "If there is no coordinator" in text
    assert "Never claim a handoff succeeded without delivery evidence" in text
    assert "not every tiny implementation subtask" in text
    assert "Do not impose an arbitrary changed-line/file cap" in text
    assert "Aim <400 LOC changed, hard stop 800" not in text


@pytest.mark.parametrize(
    "profile,permission,isolation", [
        ("cloud", "acceptEdits", "worktree"),
        ("kerrigan", "default", "inherit"),
    ],
)
def test_real_profiles_keep_permissions_and_loadable_mcp_shape(profile, permission, isolation):
    text = (PROFILES / f"{profile}.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["mcp-servers"] == {}
    assert frontmatter["permissionMode"] == permission
    assert frontmatter["isolation"] == isolation


@pytest.mark.parametrize(
    "path",
    [
        "AGENTS.md", "README.md", ".github/agents/README.md",
        ".github/agents/cloud.md", ".github/agents/kerrigan.md",
        "docs/operations/cli-reference.md", "docs/onboarding/setup.md",
        "playbooks/v2-bootstrap.md", "tools/bootstrap.sh",
        "tools/cli/kerrigan/kerrigan_cli/commands/agent.py",
        "tools/cli/kerrigan/README.md", "playbooks/upgrade-to-v2.md",
        "preset/kerrigan/plan-template.md", ".github/skills/README.md",
        "specs/kerrigan-v2/000-vision.md", "specs/kerrigan-v2/010-phases.md",
        "specs/kerrigan-v2/050-delegation-rubric.md", "tools/suggest-waves.ps1",
    ],
)
def test_active_startup_surfaces_do_not_advertise_absent_profile(path):
    text = ROOT.joinpath(*path.split("/")).read_text(encoding="utf-8")
    for obsolete in (
        "kerrigan agent local", "@local", "agents/local.md",
        "`local` profile", "`local` agent", "local profile",
        "local,cloud,kerrigan", "local, cloud, kerrigan", "local addresses feedback",
    ):
        assert obsolete not in text
    for profile in re.findall(r"\.github/agents/([a-z]+)\.md", text):
        assert (PROFILES / f"{profile}.md").is_file()


def test_wave_prediction_maps_both_triage_paths_to_existing_conductor():
    text = (ROOT / "tools" / "suggest-waves.ps1").read_text(encoding="utf-8")
    keyword = re.search(r"'triage\|playbooks/triage' = @\(([^)]+)\)", text)
    role = re.search(r"'role:triage'\s*\{[^}]+\$files \+= @\(([^)]+)\)", text)
    for mapping in (keyword, role):
        assert mapping is not None
        profile_paths = re.findall(r"'(\.github/agents/[^']+)'", mapping.group(1))
        assert profile_paths == [".github/agents/kerrigan.md"]
        assert ROOT.joinpath(*profile_paths[0].split("/")).is_file()


def test_independent_executor_requires_actionable_context_and_hands_off_review():
    text = (PROFILES / "cloud.md").read_text(encoding="utf-8")
    assert "If the `kerrigan` coordinator dispatched you" in text
    assert "otherwise the actionable issue/chat assignment" in text
    assert "Before implementation, require an actionable task context" in text
    assert "outcome, scope boundaries, acceptance criteria, and verification requirements" in text
    assert "selecting a profile alone is not a task assignment" in text
    assert "If required context is missing or conflicting, stop" in text
    assert "`kerrigan` conductor coordinates review response" in text
    assert "assigns implementation fixes back to the executor on the same branch" in text
    assert "If there is no coordinator, hand the PR" in text


def test_validation_claim_names_actual_entrypoints_not_dispatch_preflight():
    text = (PROFILES / "README.md").read_text(encoding="utf-8")
    assert "`kerrigan check` and the verify CI workflow" in text
    assert "current dispatch preflight does not invoke this validator" in text
    assert "validates this before dispatch" not in text
