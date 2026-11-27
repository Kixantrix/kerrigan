"""Generated routing requires sufficiently reliable, measured evidence."""
import copy
import hashlib
import io
import json
import tarfile

import pytest

from benchmarks.michael.matrix import generate


def record(model, repeat, *, passed=True, time=10, cost=None):
    return {"task": "fixture", "repeat": repeat, "model": model, "deployment_class": "cloud",
        "condition": "synthetic", "tool_host": "test", "round": "test", "family": "Implement",
        "size": {"tier": "small"}, "resolved": passed, "completion_seconds": time if passed else None,
        "tokens": {"inputTokens": 10, "outputTokens": 2}, "cost": cost,
        "peak_memory_bytes": None, "energy_joules": None,
        "failure_modes": [] if passed else ["unsupported-defect-claim"],
        "condition_sha256": "a" * 64, "source_sha256": "b" * 64, "ledger_source": "synthetic"}


def test_matrix_requires_evidence_not_just_fast_time():
    sparse = generate.build([record("fast", 1)])
    assert sparse["recommendations"]["Implement × small"]["status"] == "insufficient evidence"
    rows = [record(model, i, time=time) for model, time in (("fast", 5), ("slow", 20))
            for i in range(20)]
    rows.append(record("unreliable", 0, passed=False))
    result = generate.build(rows)
    assert result["recommendations"]["Implement × small"]["target"] == "synthetic:fast"
    cell = result["cells"]["synthetic:unreliable"]["Implement × small"]
    assert cell["median_verified_seconds"] is None
    assert cell["cost"] == {"status": "unknown", "value": None}
    assert cell["failure_modes"] == {"unsupported-defect-claim": 1}
    assert generate.build(rows, objective="cheapest")["recommendations"]["Implement × small"]["status"] == "insufficient evidence"


def test_matrix_validates_condition_and_duplicate_records():
    rows = [record("a", 1)]
    with pytest.raises(ValueError, match="duplicate"):
        generate.build([*rows, rows[0]])
    result = generate.build(rows)
    result["sources"] = []
    generate.validate(result)
    broken = copy.deepcopy(result)
    broken["cells"]["synthetic:a"]["Implement × small"]["n"] = 0
    with pytest.raises(ValueError, match="sample count"):
        generate.validate(broken)
    assert "insufficient evidence" in generate.markdown(result)


def test_matrix_seed_preserves_rounds_and_never_uses_human_time():
    rows, sources = generate.seed()
    assert len(rows) == 26 and len(sources) == 4
    assert {r["round"] for r in rows} == {"v1", "v2"}
    assert all("human" not in str(r).lower() for r in rows)
    assert sum(not r["resolved"] for r in rows) == 2
    assert all(len(r["ledger_sha256"]) == 64 and len(r["ledger_chain_head"]) == 64 for r in rows)
    failures = {r["task"]: r["failure_modes"] for r in rows if not r["resolved"]}
    assert failures == {"review-conflict-predictor-v3": ["unsupported-defect-claim"],
                        "orchestrate-voice-integration-v3": ["claimed-fix-not-implemented"]}
    priors = [row for source in sources for row in source.get("prior_attempts", [])]
    excluded = next(row for row in priors if row["task"] == "orchestrate-voice-integration-v2"
                    and row["model"] == "claude-sonnet-5.5")
    assert excluded["failure_modes"] == ["sandbox-boundary-write"]
    value = generate.build(rows)
    value["sources"] = sources
    generate.validate(value)
    assert all(r["status"] == "insufficient evidence" for r in value["recommendations"].values())


def test_matrix_rejects_inconsistent_unknowns_and_observed_counts():
    result = generate.build([record("a", 1)])
    result["sources"] = []
    for field, value in (("success_rate", 0), ("cost", {"status": "unknown", "value": 0})):
        broken = copy.deepcopy(result)
        broken["cells"]["synthetic:a"]["Implement × small"][field] = value
        with pytest.raises(ValueError, match="schema"):
            generate.validate(broken)


def test_matrix_generation_matches_committed_outputs():
    rows, sources = generate.seed()
    value = generate.build(rows)
    value["sources"] = sources
    assert json.loads((generate.HERE / "matrix.json").read_text()) == value
    assert (generate.HERE / "matrix.md").read_text() == generate.markdown(value)


def test_matrix_rejects_rehashed_but_corrupt_ledger_chain(tmp_path):
    raw = b'{"sequence":1,"previous":null,"record":{},"sha256":"' + b"0" * 64 + b'"}\n'
    path = tmp_path / "synthetic.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo("synthetic/ledger.jsonl")
        member.size = len(raw)
        archive.addfile(member, io.BytesIO(raw))
    data = {"archiveSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "members": {"synthetic/ledger.jsonl": hashlib.sha256(raw).hexdigest()}}
    with pytest.raises(ValueError, match="hash chain"):
        generate.archived_ledgers(data, path, {"synthetic/ledger.jsonl"})


def test_controlled_failure_modes_use_attribution_not_selection_prose():
    cases = [
        ({"cause": "model", "verdicts": [{"evidence": [
            {"description": "glob-overlap did not contribute to the outcome"}]}]}, "unsupported-defect-claim"),
        ({"cause": "model", "deterministicEvidence": "Independent cancelCheck: claimFixed=false"},
         "claimed-fix-not-implemented"),
        ({"cause": "model", "deterministicEvidence": "write $TMPDIR/x outside allowed paths"},
         "sandbox-boundary-write"),
        ({"cause": "harness", "nativeStop": "protocol_budget"}, "harness-cap"),
        ({"cause": "task"}, "task-caused"),
        ({"cause": "resource", "outcome": "contention-timeout"}, "contention-timeout"),
    ]
    for evidence, mode in cases:
        assert generate.failure_modes(evidence) == [mode]
    assert generate.failure_modes({"cause": "model", "reason": "latest admitted-and-run version"}) == [
        "model-failure-unclassified"]
    result = generate.build([record("a", i, passed=False) for i in range(3)])
    assert result["cells"]["synthetic:a"]["Implement × small"]["failure_modes"] == {
        "unsupported-defect-claim": 3}


def test_epoch_selection_requires_published_plan_and_matches_native_owner(tmp_path, monkeypatch):
    repository = tmp_path / "repo"
    parent = tmp_path / "owned"
    old = parent / "mbr3-v1"
    current = parent / "mbr3-tooltip-v2"
    old.mkdir(parents=True)
    current.mkdir()
    schedule = b"synthetic schedule"
    (old / "schedule.json").write_bytes(schedule)
    outcome = old / "trials/fixture/repeat-1/sonnet/outcome.json"
    attribution = old / "attribution/fixture/repeat-1/sonnet/attribution.json"
    outcome.parent.mkdir(parents=True)
    attribution.parent.mkdir(parents=True)
    outcome.write_text('{"status":"ungraded"}')
    attribution.write_text('{"cause":"harness"}')
    plan = {
        "scheduleSha256": hashlib.sha256(schedule).hexdigest(),
        "attempts": [
            {"task": "fixture", "repeat": 1, "model": "mai", "evidence_root": old.name,
             "source_epoch": "original"},
            {"task": "fixture", "repeat": 1, "model": "sonnet", "evidence_root": current.name,
             "source_epoch": "corrected"},
        ],
        "source_epochs": {"original": {"ownerSha256": "a" * 64},
                          "corrected": {"ownerSha256": "b" * 64}},
        "excluded_prior": {"task": "fixture", "repeat": 1, "model": "sonnet",
                          "outcomeSha256": hashlib.sha256(outcome.read_bytes()).hexdigest(),
                          "attributionSha256": hashlib.sha256(attribution.read_bytes()).hexdigest()},
    }
    verification = repository / "benchmarks/michael/local_transport/mbr3-tooltip-verification.json"
    verification.parent.mkdir(parents=True)
    verification.write_text(json.dumps({"primaryPlan": plan}))
    path = current / "primary-plan.json"
    path.write_text(json.dumps(plan))
    monkeypatch.setattr(generate, "ROOT", repository)

    def reader(root, *, selected):
        return [{**record(model, repeat), "task": task, "condition": "MB-R3",
                 "transport_owner_sha256": "a" * 64 if root == old else "b" * 64}
                for task, repeat, model in selected]

    monkeypatch.setattr(generate, "ledger_records", reader)
    rows, source = generate.epoch_records(path)
    assert {row["condition"] for row in rows} == {"MB-R3/original", "MB-R3/corrected"}
    assert source["prior_attempts"][0]["failure_modes"] == ["harness-error"]
    changed = copy.deepcopy(plan)
    changed["attempts"][0]["evidence_root"] = "access-only"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="differs from published"):
        generate.epoch_records(path)
    path.write_text(json.dumps(plan))
    monkeypatch.setattr(generate, "ledger_records",
                        lambda root, selected: [{**reader(root, selected=selected)[0],
                                                 "transport_owner_sha256": "c" * 64}])
    with pytest.raises(ValueError, match="native owner mismatch"):
        generate.epoch_records(path)


def test_selected_ledger_reader_does_not_publish_missing_attempts(tmp_path, monkeypatch):
    path = tmp_path / "trials/fixture/repeat-1/ledger.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    monkeypatch.setattr(generate.Ledger, "_read", lambda self, stream: ({}, None, "a" * 64))
    with pytest.raises(ValueError, match="incomplete selected"):
        generate.ledger_records(tmp_path, selected={("fixture", 1, "model")})


def test_selected_ledger_reader_keeps_attempt_identity_separate_from_token_keys(tmp_path, monkeypatch):
    batch = tmp_path / "trials/fixture/repeat-1"
    run = batch / "model"
    (run / "receipt").mkdir(parents=True)
    path = batch / "ledger.jsonl"
    path.write_bytes(b"synthetic ledger")
    (run / "collected-source.bin").write_bytes(b"final artifact")
    frozen = {"package": "fixture", "condition": "synthetic",
              "source": {"benchmarks/michael/local_transport/owner.mjs": "a" * 64}}
    outcome = {"conditionSha256": generate.condition_digest(frozen),
               "sourceSha256": hashlib.sha256(b"final artifact").hexdigest(),
               "status": "pass", "completionSeconds": 10}
    (run / "outcome.json").write_text(json.dumps(outcome))
    (run / "receipt/terminal.json").write_text(json.dumps({
        "wholeProcessQuiescent": True, "cleanupSeconds": 1,
        "usage": [{"inputTokens": 100, "outputTokens": 20}]}))
    trial = {"bundle": {"agent": {"configuration": {"value": frozen}}},
             "starts": [{}], "origin": "new_trial",
             "attempts": [{"verdict": "passed",
                           "time_to_verified_completion": {"status": "known",
                                                           "value": {"seconds": 10}}}]}
    monkeypatch.setattr(generate.Ledger, "_read",
                        lambda self, stream: ({"model": trial}, None, "b" * 64))
    monkeypatch.setattr(generate.curriculum, "meta", lambda name: {"family": "Implement"})
    monkeypatch.setattr(generate, "size", lambda name: {"tier": "small"})
    rows = generate.ledger_records(tmp_path, selected={("fixture", 1, "model")})
    assert len(rows) == 1
    assert rows[0]["tokens"] == {"inputTokens": 100, "outputTokens": 20}
