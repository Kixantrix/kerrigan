"""Static operations contracts, not runtime scheduling or locking tests."""

from pathlib import Path
import re

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "playbooks" / "session-operations.md"
TEXT = GUIDE.read_text(encoding="utf-8")
ENTRYPOINTS = [
    "AGENTS.md",
    "README.md",
    ".github/agents/README.md",
    ".github/agents/kerrigan.md",
    ".github/agents/cloud.md",
    ".github/skills/briefing-packet/SKILL.md",
    ".github/skills/delegation-rubric/SKILL.md",
    "playbooks/kickoff.md",
    "docs/onboarding/setup.md",
    "docs/onboarding/FAQ.md",
]


def section(heading):
    lines = TEXT.split(f"## {heading}\n", 1)[1].splitlines()
    result = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            break
        result.append(line)
    return "\n".join(result)


@pytest.mark.parametrize("relative", ENTRYPOINTS)
def test_operational_entrypoints_link_canonical_guide(relative):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]*session-operations\.md(?:#[^)]*)?)\)", text)
    assert links, f"{relative} must link the canonical operations guide"
    for link in links:
        assert (path.parent / link.split("#", 1)[0]).resolve() == GUIDE.resolve()
    assert re.search(r"optional.{0,35}issue|issues.{0,35}optional", text, re.I)


def test_guide_local_links_and_anchors_resolve():
    for link in re.findall(r"\]\(([^)]+)\)", TEXT):
        if "://" in link:
            continue
        target, _, anchor = link.partition("#")
        path = (GUIDE.parent / target).resolve()
        assert path.is_file(), f"Broken guide link: {link}"
        if anchor:
            headings = re.findall(r"^#+ (.+)$", path.read_text(encoding="utf-8"), re.M)
            assert anchor in [heading.lower().replace(" ", "-") for heading in headings]


@pytest.mark.parametrize("relative", ENTRYPOINTS[:8])
def test_primary_guidance_does_not_require_issue_dispatch(relative):
    text = (ROOT / relative).read_text(encoding="utf-8")
    obsolete = [
        r"\*\*Output:\*\*.*attached to the GH issue body",
        r"functional gate for cloud execution is.*assignment on the issue",
        r"3\. \*\*Create an issue\*\*",
        r"## 3\) Dispatch\s+Ask `kerrigan` to run `/kerrigan\.dispatch`",
        r"\*\*Dispatch\.\*\* `/kerrigan\.dispatch`.*for cloud",
        r"A typical flow:.*dispatches via `/kerrigan\.dispatch`",
        r"Each cloud task: one issue",
        r"second round as advisory-by-default",
    ]
    for pattern in obsolete:
        assert not re.search(pattern, text), f"{relative} reintroduced: {pattern}"


def test_dispatch_and_addendum_cover_closed_scope_and_delivery():
    dispatch = section("Dispatch one coherent outcome")
    for phrase in [
        "Touch", "Read-only", "Out of scope", "AC IDs", "test commands",
        "not universal changed-line/file/depth caps", "Role is independent of host",
        "actual base branch and SHA", "PR target", "acknowledged dispatch",
        "issue-only merge gate", "never bypass",
    ]:
        assert phrase in dispatch
    addendum = re.search(r"```markdown\n(.*?)```", dispatch, re.S).group(1)
    fields = re.findall(r"^- ([^:]+):", addendum, re.M)
    assert fields == [
        "Coordinator", "Implementation owner", "Role / host", "Base / dependency",
        "Resources", "Stop condition", "Next check",
    ]
    assert "not a change to generated Spec Kit templates" in dispatch
    assert "Older generated examples remain valid inputs" in dispatch


@pytest.mark.parametrize(
    "heading,phrases",
    [
        ("Ownership and handoff", [
            "one coordinator and one implementation owner",
            "Routine child questions go to the coordinator",
            "Read the actual pending plan or input",
            "not proof a blocked input was answered",
            "completions, blockers, and direction changes",
            "not chatter loops", "Lead transfer requires explicit acknowledgment",
            "before the old owner relinquishes responsibility",
            "old worker/process is quiescent before replacement writes",
            "do not launch competing implementation",
        ]),
        ("Bound active work and shared resources", [
            "one or two active workers", "not a service cap",
            "Existing hard budgets still apply", "file-conflict predictor",
            "GPU/device", "CPU/RAM", "ports", "Worktrees isolate files, not devices",
            "advisory reservation is not enforced locking",
            "lease expiry", "actual process exit and resource release evidence",
            "no resource scheduler is implemented",
        ]),
        ("Accountable triage", [
            "manual read-only pass first", "ownerless or stale actionable",
            "checks", "reviews", "decisions",
            "not merely an old timestamp or an idle session",
            "do not duplicate implementation", "explicit transfer protocol",
            "same current head/event/finding must not repeatedly notify",
            "A new head alone is not a new problem",
            "Idle alone never permits archive or close",
            "unpushed commits/unsaved drafts", "automations", "open PRs",
            "unresolved issues", "explicit authority", "acknowledged handoff",
        ]),
        ("Choose one automation lifecycle owner", [
            "New-session automation", "Same-session wake", "Agent merge",
            "One lifecycle owner per PR/outcome",
            "who disables/clears", "verify that it stopped",
            "creates no live schedules", "grants no new permissions",
        ]),
        ("Diagnose failure before retry", [
            "API validation", "Quota / rate limit", "Transport / timeout",
            "Authentication / authorization", "Hook / profile loader",
            "Context / handoff", "sanitized evidence",
            "Reconcile side effects before every retry",
            "bounded retries", "stop the affected path", "No hidden-cap claims",
        ]),
        ("Review convergence and completion", [
            "existing implementation owner on the same branch",
            "do not automatically become advisory",
            "configured/requested reviewer is not actual review evidence",
            "reviewed SHA", "missing, pending, stale, and current review",
            "attestation where declared", "Missing required evidence is a blocker",
            "reconcile living decisions", "exact base/head", "superseded decisions",
            "process/resource release", "automation stop",
        ]),
    ],
)
def test_operational_safeguards(heading, phrases):
    content = section(heading)
    for phrase in phrases:
        assert phrase in content, f"{heading} lost safeguard: {phrase}"


@pytest.mark.parametrize(
    "heading,keys",
    [
        ("Accountable triage", {
            "item", "owner", "expected_next_action", "last_meaningful_progress",
            "blocker", "next_check", "dedupe_key",
        }),
        ("Choose one automation lifecycle owner", {
            "scope", "lifecycle_owner", "mechanism", "max_work_per_run",
            "overlap", "idempotency", "no_op", "expiry", "stop",
        }),
    ],
)
def test_record_examples_are_complete_yaml_without_new_database(heading, keys):
    example = re.search(r"```yaml\n(.*?)```", section(heading), re.S).group(1)
    record = yaml.safe_load(example)
    assert set(record) == keys
    assert all(isinstance(value, str) and value.strip() for value in record.values())
    assert "no mandatory tracking database" in TEXT


def test_briefing_and_routing_preserve_legacy_inputs_and_role_boundary():
    briefing = (ROOT / ".github/skills/briefing-packet/SKILL.md").read_text(encoding="utf-8")
    assert "## Example (right-sized)" in briefing
    assert "# Briefing: T-042" in briefing
    assert "R-cloud-default" in briefing
    assert "generator and older examples below are unchanged" in briefing
    assert "do not populate or enforce this operational state" in briefing
    rubric = (ROOT / ".github/skills/delegation-rubric/SKILL.md").read_text(encoding="utf-8")
    assert "## Default: cloud" in rubric
    assert "Routing chooses a **host**, not a behavioral role or dispatch transport" in rubric
    assert "actual process exit/resource release, not lease expiry" in rubric
