"""AC-MB-003/004/005 contract portions: integration, cloud-linux, synthetic only."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

CONTRACTS = Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "contracts"
sys.path.insert(0, str(CONTRACTS))
from manifests import (
    ManifestError, manifest_reference, validate_bundle, validate_manifest,
)


def known(value, source="synthetic-receipt"):
    return {"status": "known", "value": value, "source": source}


def unavailable(status="unknown"):
    return {"status": status, "reason": "synthetic unavailable control", "source": "fixture"}


def descriptor(kind):
    return {"schema_version": 1, "kind": kind, "id": f"synthetic-{kind}",
            "revision": "1", "provenance": {"source_id": "synthetic-only"}}


def elapsed(seconds=12, scope="end_to_end", **changes):
    return known({"seconds": seconds, "scope": scope, "clock": "monotonic",
                  "host_ids": ["synthetic-host"], "coverage": "complete", **changes})


@pytest.fixture
def bundle():
    task = {**descriptor("task"), "base": {"uri": "fixture:base", "sha256": "a" * 64},
            "agent_material": [{"uri": "fixture:requirements", "sha256": "b" * 64,
                                "audience": "requirement_only"}],
            "verifier_material": [{"uri": "fixture:held-out", "sha256": "c" * 64,
                                   "audience": "verifier_only"}]}
    target = {**descriptor("target"), "requested_identity": "synthetic-model",
              "observed_identity": unavailable(), "runtime": unavailable()}
    agent = {**descriptor("agent"),
             "harness": {"id": "fixture-harness", "revision": "1", "sha256": "d" * 64},
             "configuration": unavailable()}
    condition = {**descriptor("condition"),
                 **{name: manifest_reference(value) for name, value in
                    (("task", task), ("target", target), ("agent", agent))},
                 "hosts": {role: unavailable() for role in ("inference", "agent", "verifier")},
                 "track": "practical_system", "retry_policy": "no_automatic_retries",
                 "budgets": {"active_safety_seconds": known(3600), "response_tokens": unavailable("unsupported"),
                             "reasoning_tokens": unavailable("unsupported"), "attempt_limit": known(1)},
                 "cache_policy": unavailable("unsupported"),
                 "capabilities": {"synthetic_tool": known(True), "weights": unavailable("not_applicable")},
                 "observability": {"provider_identity": unavailable(), "credits": unavailable()},
                 "required_semantics": ["synthetic_tool"]}
    attempt = {"id": "attempt-1", "verdict": "passed", "state": "completed", "stop_reason": "success",
               "verifier": {"status": "passed", "independent": True, "source": "synthetic-verifier"},
               "events": [], "timing": {"agent_work": elapsed(8, "agent_work"),
                                        "verification": elapsed(2, "verification"),
                                        "end_to_end": elapsed()},
               "time_to_verified_completion": elapsed(), "usage": {"tokens": unavailable()}}
    result = {**descriptor("result"), "condition": manifest_reference(condition), "attempts": [attempt]}
    return dict(task=task, target=target, agent=agent, condition=condition, result=result)


def test_roundtrip_freezes_descriptors_without_claiming_runtime_proof(bundle):
    original = deepcopy(bundle)
    validated = validate_bundle(**json.loads(json.dumps(bundle)))
    assert validated == original
    assert validated["target"]["observed_identity"]["status"] == "unknown"
    assert validated["condition"]["budgets"]["response_tokens"]["status"] == "unsupported"
    assert validated["condition"]["capabilities"]["weights"]["status"] == "not_applicable"
    validated["task"]["base"]["uri"] = "caller-mutation"
    assert bundle == original
    assert manifest_reference(bundle["task"]) == manifest_reference(dict(reversed(list(bundle["task"].items()))))


def test_observed_identity_can_differ_and_phase_provenance_is_retained(bundle):
    bundle.pop("result")
    bundle["target"]["observed_identity"] = known("different-synthetic-model", "native-selection-receipt")
    bundle["target"]["runtime"] = known("synthetic-runtime@2")
    bundle["condition"]["target"] = manifest_reference(bundle["target"])
    bundle["condition"]["hosts"] = {role: known(f"synthetic-{role}-host") for role in
                                    ("inference", "agent", "verifier")}
    assert validate_bundle(**bundle)["target"] == bundle["target"]
    result = {**descriptor("result"), "condition": manifest_reference(bundle["condition"]),
              "attempts": [{"id": "ungraded", "verdict": "ungraded", "state": "stopped",
                            "stop_reason": "timeout", "verifier": {
                                "status": "not_run", "independent": False, "source": "fixture"},
                            "events": [], "usage": {}, "timing": {
                                phase: elapsed(1, phase, coverage="partial") for phase in
                                ("queue", "provisioning", "setup", "agent_work", "verification", "end_to_end")}}]}
    assert validate_bundle(**bundle, result=result)["result"] == result


@pytest.mark.parametrize("track", ["practical_system", "controlled_capability", "harness_configuration"])
def test_tracks_and_asymmetric_controls_are_explicit(bundle, track):
    condition = bundle["condition"]
    condition["track"] = track
    condition["budgets"]["response_tokens"] = known(250)
    condition["budgets"]["reasoning_tokens"] = known(700)
    bundle.pop("result")
    assert validate_bundle(**bundle)["condition"] == condition


@pytest.mark.parametrize("name", ["task", "target", "agent", "condition"])
@pytest.mark.parametrize("field,value", [("id", "other"), ("revision", "2"), ("sha256", "0" * 64)])
def test_incompatible_frozen_references_fail(bundle, name, field, value):
    owner = bundle["result"] if name == "condition" else bundle["condition"]
    owner[name][field] = value
    with pytest.raises(ManifestError, match=f"{name}: incompatible"):
        validate_bundle(**bundle)


@pytest.mark.parametrize("status", ["unknown", "unsupported", "not_applicable", "false", "missing"])
def test_required_semantics_never_silently_drop(bundle, status):
    condition = bundle["condition"]
    if status == "missing":
        condition["capabilities"].pop("synthetic_tool")
    else:
        condition["capabilities"]["synthetic_tool"] = known(False) if status == "false" else unavailable(status)
    with pytest.raises(ManifestError, match="required capability"):
        validate_manifest(condition)


@pytest.mark.parametrize("change", ["audience", "overlap", "content_overlap", "digest", "empty", "extra", "version", "null", "invented"])
def test_malformed_or_unsupported_contracts_are_actionable(bundle, change):
    value = bundle["task"]
    if change == "audience":
        value["agent_material"][0]["audience"] = "verifier_only"
    elif change == "overlap":
        value["agent_material"][0]["uri"] = value["verifier_material"][0]["uri"]
    elif change == "content_overlap":
        value["agent_material"][0]["sha256"] = value["verifier_material"][0]["sha256"]
    elif change == "digest":
        value["base"]["sha256"] = "not-a-digest"
    elif change == "empty":
        value["verifier_material"] = []
    elif change == "extra":
        value["silently_ignored_control"] = True
    elif change == "version":
        value["schema_version"] = True
    else:
        value = bundle["target"]
        value["observed_identity"] = known(None) if change == "null" else {**unavailable(), "value": 0}
    with pytest.raises(ManifestError):
        validate_manifest(value)


@pytest.mark.parametrize("stop,state,status,category", [
    ("response_cap", "stopped", "not_run", "runtime"),
    ("timeout", "stopped", "not_run", "safety"),
    ("interruption", "interrupted", "not_run", "infrastructure"),
    ("evaluator_error", "stopped", "error", "infrastructure"),
    ("cancellation", "stopped", "not_run", "safety"),
    ("runtime_error", "stopped", "not_run", "runtime"),
    ("infrastructure_error", "stopped", "not_run", "infrastructure"),
    ("safety_stop", "stopped", "not_run", "safety"),
    ("agent_finished", "completed", "failed", "runtime"),
])
def test_incomplete_and_failed_attempts_retain_elapsed_not_completion(bundle, stop, state, status, category):
    result = bundle["result"]
    attempt = result["attempts"][0]
    attempt.update(stop_reason=stop, state=state, verdict="failed" if status == "failed" else "ungraded")
    attempt["verifier"]["status"] = status
    attempt["time_to_verified_completion"] = unavailable()
    code = "http_200_stream_error" if stop == "runtime_error" else stop
    attempt["events"] = [{"category": category, "code": code, "source": "fixture-native-event"}]
    checked = validate_bundle(**bundle)["result"]["attempts"][0]
    assert checked["timing"]["end_to_end"]["value"]["seconds"] == 12
    assert checked["time_to_verified_completion"]["status"] == "unknown"
    assert checked["events"] == attempt["events"]
    attempt["time_to_verified_completion"] = elapsed()
    with pytest.raises(ManifestError, match="only independently verified success"):
        validate_manifest(result)


def test_cap_can_have_independent_pass_without_becoming_completed_success(bundle):
    attempt = bundle["result"]["attempts"][0]
    attempt.update(state="stopped", stop_reason="response_cap")
    attempt.pop("time_to_verified_completion")
    assert validate_manifest(bundle["result"])["attempts"][0]["verdict"] == "passed"


@pytest.mark.parametrize("change", ["self_grade", "ungraded", "interrupted", "false_success", "partial", "different_elapsed"])
def test_inconsistent_completion_claims_fail(bundle, change):
    attempt = bundle["result"]["attempts"][0]
    if change == "self_grade":
        attempt["verifier"]["independent"] = False
    elif change == "ungraded":
        attempt["verifier"]["status"] = "not_run"
    elif change == "interrupted":
        attempt["state"] = "interrupted"
    elif change == "false_success":
        attempt.update(verdict="failed")
        attempt["verifier"]["status"] = "failed"
    elif change == "partial":
        attempt["time_to_verified_completion"]["value"]["coverage"] = "partial"
    else:
        attempt["time_to_verified_completion"] = elapsed(13)
    with pytest.raises(ManifestError):
        validate_manifest(bundle["result"])


@pytest.mark.parametrize("number", [-1, float("nan"), float("inf"), True, "12"])
@pytest.mark.parametrize("location", ["timing", "budget", "usage"])
def test_invalid_durations_and_counts_fail(bundle, number, location):
    if location == "budget":
        value = bundle["condition"]
        value["budgets"]["active_safety_seconds"] = known(number)
    else:
        value = bundle["result"]
        attempt = value["attempts"][0]
        if location == "timing":
            attempt["timing"]["agent_work"] = elapsed(number, "agent_work")
        else:
            attempt["usage"]["tokens"] = known(number)
    with pytest.raises(ManifestError):
        validate_manifest(value)


def test_cross_host_timing_needs_correlation_not_monotonic_subtraction(bundle):
    attempt = bundle["result"]["attempts"][0]
    attempt.pop("time_to_verified_completion")
    attempt["timing"]["end_to_end"] = elapsed(host_ids=["agent-host", "verifier-host"])
    with pytest.raises(ManifestError, match="cross-host monotonic"):
        validate_manifest(bundle["result"])
    attempt["timing"]["end_to_end"]["value"]["clock"] = "correlated_wall"
    with pytest.raises(ManifestError, match="correlation_id"):
        validate_manifest(bundle["result"])
    attempt["timing"]["end_to_end"]["value"]["correlation_id"] = "fixture-clock-correlation"
    attempt["time_to_verified_completion"] = deepcopy(attempt["timing"]["end_to_end"])
    assert validate_manifest(bundle["result"])["attempts"] == [attempt]


def test_timing_scope_and_correlated_duration_inconsistency_fail(bundle):
    attempt = bundle["result"]["attempts"][0]
    attempt["timing"]["agent_work"] = elapsed(13, "agent_work")
    with pytest.raises(ManifestError, match="exceeds complete end-to-end"):
        validate_manifest(bundle["result"])
    attempt["timing"]["agent_work"] = elapsed(8, "verification")
    with pytest.raises(ManifestError, match="scope"):
        validate_manifest(bundle["result"])


@pytest.mark.parametrize("value", [None, [], {"kind": "future"}, {"kind": "task", "provenance": {"bad": {1: "value"}}}])
def test_non_json_or_wrong_manifest_shapes_raise_contract_errors(value):
    with pytest.raises(ManifestError):
        validate_manifest(value)


def test_circular_input_is_an_actionable_error(bundle):
    value = bundle["task"]
    value["provenance"]["cycle"] = value
    with pytest.raises(ManifestError, match="circular"):
        validate_manifest(value)


def test_absent_timing_stays_unknown_and_safety_cutoff_is_not_completion(bundle):
    attempt = bundle["result"]["attempts"][0]
    attempt["timing"] = {"setup": unavailable()}
    attempt.pop("time_to_verified_completion")
    checked = validate_bundle(**bundle)
    assert checked["result"]["attempts"][0]["timing"] == {"setup": unavailable()}
    assert "time_to_verified_completion" not in checked["result"]["attempts"][0]
    assert checked["condition"]["budgets"]["active_safety_seconds"]["value"] == 3600
    assert checked["result"]["attempts"][0]["usage"]["tokens"] == unavailable()


def test_all_attempts_preserved_including_retry_and_infrastructure_failure(bundle):
    result = bundle["result"]
    first = result["attempts"][0]
    retry = deepcopy(first)
    retry.update(id="attempt-2", retry_of="attempt-1")
    first.update(verdict="ungraded", state="stopped", stop_reason="evaluator_error")
    first["verifier"]["status"] = "error"
    first["time_to_verified_completion"] = unavailable()
    first["events"] = [{"category": "infrastructure", "code": "verifier_crash", "source": "fixture"}]
    result["attempts"].append(retry)
    assert validate_manifest(result)["attempts"] == [first, retry]
    retry["retry_of"] = "missing"
    with pytest.raises(ManifestError, match="earlier retained attempt"):
        validate_manifest(result)
    retry["retry_of"] = "attempt-1"
    retry["id"] = "attempt-1"
    with pytest.raises(ManifestError, match="duplicate attempt"):
        validate_manifest(result)
