#!/usr/bin/env python3
"""Tests for docs/test-strategy.md."""

from pathlib import Path

import pytest
import yaml


DOC = Path(__file__).resolve().parent.parent / "docs" / "test-strategy.md"
EXPECTED_BOUNDARIES = {
    "Incorrect transform or error handling": (
        "Expected values and typed errors",
        "All assertions pass, including invalid input",
    ),
    "Broken model interface": (
        "Pinned tiny fixture reference shapes, dtypes and error cases",
        "Exact shape/dtype; output tolerance <= 1e-6",
    ),
    "Broken service or transitive consumer": (
        "Consumer contract against changed producer",
        "All affected contracts pass",
    ),
    "Unbuildable or unlaunchable application": (
        "Normal build/package and launch happy path",
        "Build/package exit 0 and health assertion passes",
    ),
    "Broken user workflow": (
        "Real interface checkpoints and persisted end state",
        "All affected journey assertions pass",
    ),
    "Real model quality regression": (
        "Real pinned checkpoint on versioned evaluation set",
        "Example accuracy >= 0.90",
    ),
    "Device correctness or performance regression": (
        "Real target backend/device against reference and timing budget",
        "Example max error <= 1e-4 and p95 <= 50 ms",
    ),
    "Outcome requires human judgment": (
        "Named review rubric and qualified reviewer",
        "All rubric criteria accepted",
    ),
}


def section(heading):
    return DOC.read_text(encoding="utf-8").split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def test_doc_present_and_has_sections():
    repo_root = Path(__file__).resolve().parent.parent
    doc = repo_root / "docs" / "test-strategy.md"
    assert doc.exists(), "docs/test-strategy.md must exist"

    content = doc.read_text(encoding="utf-8")
    assert len(content.splitlines()) <= 300
    assert "unit" in content and "integration" in content and "smoke" in content and "e2e" in content and "scenario" in content
    assert "cloud-linux" in content
    assert "cloud-windows" in content
    assert "cloud-macos" in content
    assert "cloud-self-hosted-<name>" in content
    assert "local-attested-<class>" in content
    assert "manual-human" in content
    assert "Decision tree" in content
    assert "test-ladder" in content
    assert "test-environment" in content
    assert "e2e-test" in content
    assert "scenario-test" in content


def assert_matrix_contract(content):
    lines = [line for line in content.splitlines() if line.startswith("|")]
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines]
    assert rows[0] == ["Risk", "Oracle", "Threshold", "Level", "Environment", "Trigger", "Evidence"]
    assert len(rows[2:]) == len(EXPECTED_BOUNDARIES)
    assert {row[0] for row in rows[2:]} == EXPECTED_BOUNDARIES.keys()
    for risk, oracle, threshold, level, environment, trigger, evidence in rows[2:]:
        assert all((risk, oracle, threshold, trigger, evidence))
        assert (oracle, threshold) == EXPECTED_BOUNDARIES[risk], f"{risk}: oracle/threshold boundary"
        assert level in {"unit", "integration", "smoke", "e2e", "scenario"}
        assert environment in {
            "cloud-linux", "cloud-windows", "cloud-self-hosted-model-eval",
            "local-attested-accelerator", "manual-human",
        }
    by_risk = {row[0]: dict(zip(rows[0], row)) for row in rows[2:]}
    device = by_risk["Device correctness or performance regression"]
    assert device["Environment"] == "local-attested-accelerator"


def test_risk_matrix_has_complete_single_axis_rows():
    assert_matrix_contract(section("Risk, trigger and evidence matrix"))


def test_matrix_example_environments_require_registered_capable_verifiers():
    content = " ".join(section("Risk, trigger and evidence matrix").split())
    for phrase in [
        "`cloud-self-hosted-model-eval` and `local-attested-accelerator` are illustrative",
        "not registered verifier claims",
        "replace its environment with a capability-matching ID",
        "declared in the applicable manifest's `supported_environments`",
        "validation requires exact membership",
        "explicitly register that ID only when a capable verifier is actually available",
        "Do not add fictitious hosts or select a mismatched device merely to pass validation",
        "block or arrange a handoff without claiming completion",
    ]:
        assert phrase in content, f"Environment examples must retain: {phrase}"


@pytest.mark.parametrize("risk", EXPECTED_BOUNDARIES)
@pytest.mark.parametrize("column", [1, 2], ids=["oracle", "threshold"])
@pytest.mark.parametrize("placeholder", ["TBD", "<placeholder>"])
def test_matrix_rejects_unmeasurable_boundaries_in_every_row(risk, column, placeholder):
    lines = section("Risk, trigger and evidence matrix").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"| {risk} |"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            cells[column] = placeholder
            lines[index] = "| " + " | ".join(cells) + " |"
            break
    else:
        pytest.fail(f"Missing matrix row: {risk}")
    with pytest.raises(AssertionError, match="oracle/threshold boundary"):
        assert_matrix_contract("\n".join(lines))


def test_evidence_template_captures_reproducible_identity_and_result():
    content = section("Evidence record and validity")
    record = yaml.safe_load(content.split("```yaml\n", 1)[1].split("```", 1)[0])
    required = {
        "ac_id", "test_id", "risk", "oracle", "threshold", "level", "environment",
        "trigger", "tested_commit", "worktree_state", "patch_digest", "inputs",
        "runtime_device", "test_policy_version", "command", "measurement_conditions",
        "result", "observed", "logs", "executed_at", "verifier", "retention",
    }
    assert required <= record.keys()
    assert all(record[key] for key in required)
    assert record["tested_commit"] == "<full-commit-sha>"
    assert record["worktree_state"] == "<clean-or-dirty>"
    assert set(record["inputs"]) == {"model", "data", "fixture", "artifact"}
    assert all("sha256" in identity for identity in record["inputs"].values())
    assert "sha256" in record["patch_digest"] and "sha256" in record["logs"]
    assert "owner-access-policy-and-expiry" in record["retention"]


@pytest.mark.parametrize(("heading", "required_phrases"), [
    ("Affected consumers and conservative fallback", [
        "affected transitive consumers", "unit/contract/integration",
        "Shared code/schema/config", "dependency manifests/lockfiles",
        "build/toolchain", "workflows and selection-policy",
        "missing/stale graph", "failed diff/planning", "unclassified",
        "run broader tests, not pass", "existing broad suite",
        "block or hand off", "skip, cancellation, missing result",
        "build/packaging checks", "Scheduled deep tests supplement, not replace",
    ]),
    ("Model fixtures and real target checks", [
        "tiny deterministic fixtures", "SHA-256", "provenance/license",
        "input/reference-output digests", "verify checksums before use",
        "Reuse unchanged pinned artifacts", "new identity",
        "Tiny fixtures do not establish real-checkpoint quality",
        "real change-critical model/device checks", "preprocessing/tokenizer",
        "quantization/precision", "runtime/driver", "pending attestation",
        "seeds, warmup, sample count",
    ]),
    ("Evidence record and validity", [
        "New code or inputs invalidate evidence by default",
        "Dirty-worktree evidence requires the exact patch",
        "Retest the combined merge candidate", "merge_group",
        "relevant-input equivalence policy", "combined-source integration",
        "pending-attestation: <ac-id>", "authorized verifier",
        "Missing logs, mismatched SHA/model/input, stale or unauthorized",
        "not cryptographic assurance",
        "current attestation parser does not enforce all these fields",
    ]),
    ("Shadow selection before gate reduction", [
        "shadow alongside unchanged broad gates", "10 candidate PRs",
        "does not run that pilot", "selected and omitted checks with reasons",
        "false negatives", "execution time separately from queue time",
        "runner/OS cost", "same source and inputs",
        "incomplete broad runs are inconclusive",
        "Stop expansion on any missed relevant failure",
        "tested dependency rules", "explicit direction decision",
        "rollback restoring broad gates", "not proof of safety",
        "reject failed planning, absent evidence",
        "failed/cancelled/incorrectly skipped required jobs",
        "merge_group", "Never return unconditional success",
    ]),
])
def test_safety_boundaries_are_explicit(heading, required_phrases):
    content = " ".join(section(heading).split())
    for phrase in required_phrases:
        assert phrase in content, f"{heading} must retain: {phrase}"


def test_document_does_not_claim_runtime_enforcement():
    content = " ".join(DOC.read_text(encoding="utf-8").split())
    assert "not an implemented affected-test selector or stronger attestation validator" in content
    assert "Existing required checks remain unchanged" in content
