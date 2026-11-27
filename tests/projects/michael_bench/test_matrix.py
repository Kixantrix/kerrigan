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
    rows, sources = generate.default_records()
    value = generate.build(rows)
    value["sources"] = sources
    assert json.loads((generate.HERE / "matrix.json").read_text()) == value
    assert (generate.HERE / "matrix.md").read_text() == generate.markdown(value)


def test_sealed_epoch_archive_reproduces_without_owned_paths_and_rejects_members(tmp_path, monkeypatch):
    folder = tmp_path / "benchmarks/michael/curriculum"
    folder.mkdir(parents=True)
    path = folder / "MBR3-core-verification.json"
    archive = folder / "MBR3-core-evidence.tar.gz"
    plan = "mbr3-discovery-v4/primary-plan.json"
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    monkeypatch.setattr(generate, "epoch_records",
                        lambda value: ([record("model", 1)], {"path": "synthetic published epoch"}))
    for member_name, bad_digest in ((plan, False), (plan, True), ("../escape", False)):
        raw = b"synthetic immutable plan"
        with tarfile.open(archive, "w:gz") as target:
            member = tarfile.TarInfo(member_name)
            member.size = len(raw)
            target.addfile(member, io.BytesIO(raw))
        path.write_text(json.dumps({
            "archiveFile": archive.name, "archiveSha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "primaryPlanPath": plan, "members": {
                member_name: "0" * 64 if bad_digest else hashlib.sha256(raw).hexdigest()}}))
        if bad_digest or member_name != plan:
            with pytest.raises(ValueError, match="archived member mismatch|archive member denied"):
                generate.sealed_epoch_records(path)
        else:
            rows, sources = generate.sealed_epoch_records(path)
            assert rows == [record("model", 1)] and len(sources) == 3
    row = {**record("model", 1), "ledger_sha256": "a" * 64}
    with pytest.raises(ValueError, match="ledger slot across conditions"):
        generate.build([row, {**row, "condition": "renamed"}])


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
        ({"cause": "model", "verdicts": [{"evidence": [
            {"description": "glob-overlap was a false-positive review finding"}]}]}, "unsupported-defect-claim"),
        ({"cause": "model", "deterministicEvidence": "Independent cancelCheck: claimFixed=false"},
         "claimed-fix-not-implemented"),
        ({"cause": "model", "deterministicEvidence": "unsupported auth-bypass claim"},
         "unsupported-defect-claim"),
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


def test_split_attribution_requires_hash_bound_published_resolution(tmp_path, monkeypatch):
    repository, root = tmp_path / "repo", tmp_path / "mbr3-discovery-v4"
    run = root / "trials/fixture/repeat-2/model"
    panel = root / "attribution/fixture/repeat-2/model/attribution.json"
    panel.parent.mkdir(parents=True)
    panel.write_text('{"cause":"unresolved","verdicts":[{"cause":"model"},{"cause":"task"}]}')
    (run / "independent-grader").mkdir(parents=True)
    for name in ("outcome.json", "collected-source.bin", "independent-grader/report.json"):
        (run / name).write_bytes(b"synthetic immutable evidence")
    destination = repository / "benchmarks/michael/curriculum/MBR3-fixture-resolution.json"
    destination.parent.mkdir(parents=True)
    monkeypatch.setattr(generate, "ROOT", repository)
    assert generate.resolved_attribution(root, "fixture", 2, "model", run)[0]["cause"] == "unresolved"
    receipt = {"kind": "deterministic-attribution-resolution",
               "task": "fixture", "repeat": 2, "model": "model", "evidence_root": root.name,
               "cause": "model", "counts_as_model_failure": True, "subject_rerun": False,
               "failure_modes": ["unsupported-defect-claim"],
               "evidence": ["unsupported auth-bypass claim"]}
    bindings = {"originalPanelSha256": panel, "outcomeSha256": run / "outcome.json",
                "collectedArtifactsSha256": run / "collected-source.bin",
                "graderReportSha256": run / "independent-grader/report.json"}
    receipt.update({key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in bindings.items()})
    destination.write_text(json.dumps(receipt))
    resolved, digest = generate.resolved_attribution(root, "fixture", 2, "model", run)
    assert resolved["cause"] == "model" and generate.failure_modes(resolved) == ["unsupported-defect-claim"]
    assert digest == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert json.loads(panel.read_bytes())["cause"] == "unresolved"
    (run / "collected-source.bin").write_bytes(b"changed")
    with pytest.raises(ValueError, match="resolution mismatch"):
        generate.resolved_attribution(root, "fixture", 2, "model", run)


@pytest.mark.parametrize("epoch", ["tooltip", "parity", "discovery"])
def test_epoch_selection_requires_published_plan_and_matches_native_owner(tmp_path, monkeypatch, epoch):
    repository = tmp_path / "repo"
    parent = tmp_path / "owned"
    old = parent / "mbr3-v1"
    current = parent / {"tooltip": "mbr3-tooltip-v2", "parity": "mbr3-parity-v3",
                        "discovery": "mbr3-discovery-v4"}[epoch]
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
    source_maps = {}
    for root, owner in ((old, "a" * 64), (current, "b" * 64)):
        source_maps[root] = {"benchmarks/michael/local_transport/owner.mjs": owner}
        (root / "safety.json").write_text(json.dumps({"passed": True, "source": source_maps[root]}))
    plan = {
        "scheduleSha256": hashlib.sha256(schedule).hexdigest(),
        "attempts": [
            {"task": "fixture", "repeat": 1, "model": "mai", "evidence_root": old.name,
             "source_epoch": "original"},
            {"task": "fixture", "repeat": 1, "model": "sonnet", "evidence_root": current.name,
             "source_epoch": "corrected"},
        ],
        "source_epochs": {"original": {"ownerSha256": "a" * 64,
                                      "safetySha256": hashlib.sha256((old / "safety.json").read_bytes()).hexdigest()},
                          "corrected": {"ownerSha256": "b" * 64,
                                        "safetySha256": hashlib.sha256((current / "safety.json").read_bytes()).hexdigest()}},
        "excluded_prior": {"task": "fixture", "repeat": 1, "model": "sonnet",
                          "outcomeSha256": hashlib.sha256(outcome.read_bytes()).hexdigest(),
                          "attributionSha256": hashlib.sha256(attribution.read_bytes()).hexdigest()},
    }
    if epoch != "tooltip":
        prior = plan.pop("excluded_prior")
        plan["excluded_priors"] = [{**prior, "failure_modes": ["invented-path-read"],
                                   "behavior": "invented-path-read", "cutoff": "harness-policy"}]
    verification = repository / "benchmarks/michael/local_transport" / f"mbr3-{epoch}-verification.json"
    verification.parent.mkdir(parents=True)
    if epoch == "discovery":
        sweep = verification.with_name("mbr3-discovery-parity.json")
        sweep.write_bytes(b"synthetic sweep")
        plan["paritySweepSha256"] = hashlib.sha256(sweep.read_bytes()).hexdigest()
    verification.write_text(json.dumps({"primaryPlan": plan}))
    path = current / "primary-plan.json"
    path.write_text(json.dumps(plan))
    monkeypatch.setattr(generate, "ROOT", repository)

    def reader(root, *, selected):
        return [{**record(model, repeat), "task": task, "condition": "MB-R3",
                 "transport_source_sha256": generate.condition_digest(source_maps[root]),
                 "transport_owner_sha256": "a" * 64 if root == old else "b" * 64}
                for task, repeat, model in selected]

    monkeypatch.setattr(generate, "ledger_records", reader)
    rows, source = generate.epoch_records(path)
    assert {row["condition"] for row in rows} == {"MB-R3/original", "MB-R3/corrected"}
    assert source["prior_attempts"][0]["failure_modes"] == [
        "harness-error" if epoch == "tooltip" else "invented-path-read"]
    assert source["prior_attempts"][0]["provenance"]["excluded_from_task_failures"] is True
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


@pytest.mark.parametrize("variant", ["complete", "incomplete", "schedule-mismatch", "alias"])
def test_expanded_epoch_requires_complete_hash_bound_cohort_schedules(tmp_path, monkeypatch, variant):
    repository, parent = tmp_path / "repo", tmp_path / "owned"
    roots = [parent / "mbr3-v1", parent / "mbr3-expanded-v5"]
    plan = {"attempts": [], "source_epochs": {}, "cohortSchedules": [], "excluded_priors": []}
    sources = {}
    for index, root in enumerate(roots):
        root.mkdir(parents=True)
        task, model, epoch = f"fixture-{index}", f"model-{index}", f"epoch-{index}"
        schedule = json.dumps([{"task": task, "repeat": 1, "models": [model]}]).encode()
        (root / "schedule.json").write_bytes(schedule)
        sources[root] = {"benchmarks/michael/local_transport/owner.mjs": str(index) * 64}
        safety = json.dumps({"passed": True, "source": sources[root]}).encode()
        (root / "safety.json").write_bytes(safety)
        plan["cohortSchedules"].append({"evidence_root": root.name,
                                       "sha256": hashlib.sha256(schedule).hexdigest()})
        plan["source_epochs"][epoch] = {"ownerSha256": str(index) * 64,
                                       "safetySha256": hashlib.sha256(safety).hexdigest()}
        plan["attempts"].append({"task": task, "repeat": 1, "model": model,
                                 "evidence_root": root.name, "source_epoch": epoch})
    plan["scheduleSha256"] = plan["cohortSchedules"][0]["sha256"]
    if variant == "incomplete":
        plan["attempts"].pop()
    elif variant == "schedule-mismatch":
        (roots[1] / "schedule.json").write_bytes(b"changed schedule")
    elif variant == "alias":
        plan["cohortSchedules"][1]["evidence_root"] = "../access-only"
    verification = repository / "benchmarks/michael/local_transport/mbr3-expanded-verification.json"
    verification.parent.mkdir(parents=True)
    verification.write_text(json.dumps({"primaryPlan": plan}))
    path = roots[1] / "primary-plan.json"
    path.write_text(json.dumps(plan))
    monkeypatch.setattr(generate, "ROOT", repository)
    monkeypatch.setattr(generate, "ledger_records", lambda root, selected: [
        {**record(model, repeat), "task": task, "condition": "MB-R3",
         "transport_source_sha256": generate.condition_digest(sources[root]),
         "transport_owner_sha256": sources[root]["benchmarks/michael/local_transport/owner.mjs"]}
        for task, repeat, model in selected])
    if variant == "complete":
        rows, _ = generate.epoch_records(path)
        assert len(rows) == 2
        assert {row["condition"] for row in rows} == {"MB-R3/epoch-0", "MB-R3/epoch-1"}
    else:
        expected = {"incomplete": "incomplete.*selection", "schedule-mismatch": "cohort schedule mismatch",
                    "alias": "cohort alias denied"}[variant]
        with pytest.raises(ValueError, match=expected):
            generate.epoch_records(path)


@pytest.mark.parametrize("local", [False, True])
def test_selected_ledger_reader_keeps_attempt_identity_separate_from_token_keys(tmp_path, monkeypatch, local):
    batch = tmp_path / "trials/fixture/repeat-1"
    run = batch / "model"
    (run / "receipt").mkdir(parents=True)
    path = batch / "ledger.jsonl"
    path.write_bytes(b"synthetic ledger")
    (run / "collected-source.bin").write_bytes(b"final artifact")
    frozen = {"package": "fixture", "condition": "synthetic",
              "source": {"benchmarks/michael/local_transport/owner.mjs": "a" * 64}}
    if local:
        frozen["localInference"] = {"model": "model"}
    outcome = {"conditionSha256": generate.condition_digest(frozen),
               "sourceSha256": hashlib.sha256(b"final artifact").hexdigest(),
               "status": "pass", "completionSeconds": 10}
    (run / "outcome.json").write_text(json.dumps(outcome))
    terminal = {
        "wholeProcessQuiescent": True, "cleanupSeconds": 1,
        "usage": [{"inputTokens": 100, "outputTokens": 20}]}
    if local:
        terminal.update(nativePrompts=0, usage="unknown", localInference={
            "release": {"ownedRequestsDrained": True},
            "events": [{"type": "local_request_finished",
                        "usage": {"inputTokens": 100, "outputTokens": 20}}]})
    (run / "receipt/terminal.json").write_text(json.dumps(terminal))
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
    assert rows[0]["deployment_class"] == ("local laptop" if local else "cloud")
    if local:
        terminal["localInference"]["release"]["ownedRequestsDrained"] = False
        (run / "receipt/terminal.json").write_text(json.dumps(terminal))
        with pytest.raises(ValueError, match="backend drain"):
            generate.ledger_records(tmp_path, selected={("fixture", 1, "model")})
