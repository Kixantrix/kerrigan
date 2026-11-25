"""AC-MB-003/004/005: synthetic filesystem integration, environment: cloud-linux."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "ledger_report"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "contracts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from api import Ledger, LedgerError, compare
from manifests import manifest_reference
from test_manifests import bundle, descriptor, elapsed, known, unavailable


def frozen(bundle, *, task="task-1", target="model-A", retries=1):
    value = deepcopy(bundle)
    value.pop("result")
    value["task"]["id"] = task
    value["target"]["id"] = target
    value["target"]["requested_identity"] = target
    condition = value["condition"]
    condition["budgets"]["attempt_limit"] = known(retries)
    condition["retry_policy"] = "declared_retries" if retries > 1 else "no_automatic_retries"
    for name in ("task", "target", "agent"):
        condition[name] = manifest_reference(value[name])
    return value


def result(value, *, attempt_id="a1", stop="success", seconds=12, retry_of=None, prior=()):
    status = "passed" if stop == "success" else "failed" if stop == "agent_finished" else (
        "error" if stop == "evaluator_error" else "not_run")
    attempt = {"id": attempt_id, **({"retry_of": retry_of} if retry_of else {}),
               "verdict": {"passed": "passed", "failed": "failed"}.get(status, "ungraded"),
               "state": "completed" if stop in {"success", "agent_finished"} else "stopped",
               "stop_reason": stop, "verifier": {"status": status, "independent": status in {"passed", "failed"},
                                                "source": "synthetic-verifier"},
               "events": [], "timing": {} if seconds is None else {
                   "setup": elapsed(1, "setup"), "agent_work": elapsed(seconds - 2, "agent_work"),
                   "verification": elapsed(1, "verification"), "end_to_end": elapsed(seconds)},
               "usage": {"price": known(2), "credits": unavailable(), "power": unavailable("not_applicable")}}
    if stop == "success" and seconds is not None:
        attempt["time_to_verified_completion"] = elapsed(seconds)
    return {**descriptor("result"), "condition": manifest_reference(value["condition"]),
            "attempts": [*deepcopy(prior), attempt]}


def add(ledger, trial, value, **changes):
    ledger.start(trial, value, attempt_id="a1", origin="synthetic")
    terminal = result(value, **changes)
    ledger.finalize(trial, terminal)
    return terminal


def comparison(ledger, a, b, *, suite=None):
    return compare(ledger, cohorts={"A": a, "B": b},
                   suite=suite or [manifest_reference(ledger.snapshot()[a[0]]["bundle"]["task"])])


def test_durable_start_terminal_idempotency_and_frozen_conflicts(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    value = frozen(bundle)
    terminal = result(value)
    with pytest.raises(LedgerError, match="start required"):
        ledger.finalize("t", terminal)
    assert ledger.start("t", value, attempt_id="a1", origin="synthetic")
    assert not ledger.start("t", deepcopy(value), attempt_id="a1", origin="synthetic")
    changed = deepcopy(value)
    changed["task"]["revision"] = "2"
    with pytest.raises(ValueError, match="incompatible"):
        ledger.start("t", changed, attempt_id="a1", origin="synthetic")
    assert Ledger(ledger.path).snapshot()["t"]["bundle"] == value
    assert ledger.finalize("t", terminal)
    assert not Ledger(ledger.path).finalize("t", terminal)
    terminal["id"] = "conflicting-terminal"
    with pytest.raises(LedgerError, match="already terminal"):
        ledger.finalize("t", terminal)
    assert len(ledger.path.read_bytes().splitlines()) == 2


def test_recovery_retains_provenance_partial_elapsed_and_is_not_new_attempt(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    value = frozen(bundle)
    ledger.start("t", value, attempt_id="a1", origin="synthetic")
    event = {"category": "runtime", "code": "native-stream-error", "source": "synthetic-receipt"}
    arguments = dict(event_id="e1", event=event,
                     timing={"end_to_end": elapsed(7, coverage="partial")},
                     artifacts=[{"uri": "synthetic:trace", "sha256": "e" * 64}])
    assert ledger.checkpoint("t", "a1", **arguments)
    assert not ledger.checkpoint("t", "a1", **arguments)
    assert Ledger(ledger.path).recover("t")
    assert not ledger.recover("t")
    trial = ledger.snapshot()["t"]
    assert len(trial["starts"]) == 1
    assert trial["checkpoints"][0]["artifacts"] == arguments["artifacts"]
    attempt = trial["attempts"][0]
    assert attempt["events"] == [event]
    assert attempt["state"] == "interrupted" and attempt["verdict"] == "ungraded"
    assert attempt["timing"]["end_to_end"]["value"]["seconds"] == 7
    assert attempt["time_to_verified_completion"]["status"] == "unknown"
    with pytest.raises(LedgerError, match="terminal"):
        ledger.checkpoint("t", "a1", **{**arguments, "event_id": "e2"})


@pytest.mark.parametrize("damage", ["truncate", "digest", "duplicate_key", "malformed_record"])
def test_corrupt_files_refused_without_repair(tmp_path, bundle, damage):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.start("t", frozen(bundle), attempt_id="a1", origin="synthetic")
    raw = ledger.path.read_bytes()
    if damage == "truncate":
        raw = raw[:-2]
    elif damage == "digest":
        raw = raw.replace(b'"synthetic"', b'"new_trial"')
    elif damage == "duplicate_key":
        raw = raw.replace(b'"sequence":1', b'"sequence":1,"sequence":1')
    else:
        body = {"sequence": 1, "previous": None, "record": []}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        raw = json.dumps({**body, "sha256": hashlib.sha256(canonical).hexdigest()}).encode() + b"\n"
    ledger.path.write_bytes(raw)
    with pytest.raises(LedgerError, match="corrupt|truncated"):
        ledger.snapshot()
    assert ledger.path.read_bytes() == raw


def test_retry_accounting_partial_binding_and_undefined_zero_success(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    a, b = frozen(bundle, retries=2), frozen(bundle, target="model-B", retries=2)
    failed = result(a, stop="agent_finished", seconds=20)
    ledger.start("a", a, attempt_id="a1", origin="synthetic")
    partial = {"result": manifest_reference(failed), "attempt_id": "a1", "passed": 2, "total": 3,
               "source": "held-out-fixture", "artifacts": [{"uri": "synthetic:counts", "sha256": "f" * 64}]}
    with pytest.raises(LedgerError, match="bind exact"):
        ledger.finalize("a", failed, partial={**partial, "result": manifest_reference(result(a))})
    ledger.finalize("a", failed, partial=partial)
    ledger.start("a", a, attempt_id="a2", origin="synthetic", retry_of="a1")
    ledger.finalize("a", result(a, attempt_id="a2", retry_of="a1", prior=failed["attempts"], seconds=30))
    add(ledger, "b", b, stop="timeout", seconds=40)
    report = comparison(ledger, ["a"], ["b"])
    ra, rb = report["cohorts"]["A"], report["cohorts"]["B"]
    assert (ra["started_attempts"], ra["first_attempt_verified"], ra["eventual_verified"]) == (2, 0, 1)
    assert ra["phases"]["end_to_end"]["total"] == 50
    assert ra["usage"]["price"]["total"] is None
    assert ra["partial_assertions"] == {"attempt_denominator": 2, "measured_attempts": 1,
                                      "observed_passed": 2, "observed_total": 3}
    assert rb["all_attempt_seconds_per_verified_task"] is None
    assert rb["usage"]["credits"]["total"] is None and rb["usage"]["power"]["total"] is None
    assert report["both_success_complete_time_subset"]["paired_denominator"] == 0
    assert not report["paired_tasks"][0]["B"]["verified"]
    with pytest.raises(LedgerError, match="limit"):
        ledger.start("a", a, attempt_id="a3", origin="synthetic", retry_of="a2")


def test_paired_rows_keep_failures_missing_tasks_and_incomplete_timing(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    suite = []
    for task, left, right in [("t1", 10, 15), ("t2", 20, None), ("t3", 30, 35)]:
        a, b = frozen(bundle, task=task), frozen(bundle, task=task, target="model-B")
        suite.append(manifest_reference(a["task"]))
        add(ledger, task + "a", a, seconds=left)
        if task == "t3":
            ledger.start(task + "b", b, attempt_id="a1", origin="synthetic")
        else:
            add(ledger, task + "b", b, seconds=right, stop="success" if task == "t1" else "evaluator_error")
    report = comparison(ledger, ["t1a", "t2a", "t3a"], ["t1b", "t2b", "t3b"], suite=suite)
    paired = report["both_success_complete_time_subset"]
    assert (paired["eligible_denominator"], paired["paired_denominator"]) == (3, 1)
    assert paired["differences"][0]["second_minus_first_seconds"] == 5
    assert len(report["paired_tasks"]) == 3
    rb = report["cohorts"]["B"]
    assert rb["completion_coverage"] == 1 / 3
    assert rb["states"]["unfinished"] == 1 and rb["verifier_statuses"]["error"] == 1
    assert rb["phases"]["end_to_end"]["total"] is None
    assert rb["phases"]["end_to_end"]["observed_sum"] == 15
    assert rb["usage"]["price"]["total"] is None
    missing = comparison(ledger, ["t1a"], ["t1b"], suite=suite)
    assert missing["cohorts"]["A"]["completion_coverage"] == 1 / 3
    assert missing["paired_tasks"][1]["A"]["trial_id"] is None


@pytest.mark.parametrize("change", ["budget", "harness", "configuration", "cache", "track", "origin"])
def test_incompatible_conditions_refused(tmp_path, bundle, change):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    a, b = frozen(bundle), frozen(bundle, target="model-B")
    if change == "budget":
        b["condition"]["budgets"]["active_safety_seconds"] = known(60)
    elif change == "harness":
        b["agent"]["harness"]["revision"] = "2"
    elif change == "configuration":
        b["agent"]["configuration"] = known({"different": True})
    elif change == "cache":
        b["condition"]["cache_policy"] = known("warm")
    elif change == "track":
        b["condition"]["track"] = "controlled_capability"
    b["condition"]["agent"] = manifest_reference(b["agent"])
    add(ledger, "a", a)
    ledger.start("b", b, attempt_id="a1", origin="new_trial" if change == "origin" else "synthetic")
    ledger.finalize("b", result(b))
    with pytest.raises(LedgerError, match="incompatible|controlled"):
        comparison(ledger, ["a"], ["b"])


def test_practical_host_disclosures_and_controlled_unknowns(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    a, b = frozen(bundle), frozen(bundle, target="model-B")
    b["condition"]["hosts"]["agent"] = known("different-host")
    b["condition"]["observability"]["credits"] = known("native")
    add(ledger, "a", a)
    add(ledger, "b", b)
    report = comparison(ledger, ["a"], ["b"])
    assert report["disclosures"][1]["bundle"]["condition"]["hosts"]["agent"]["value"] == "different-host"
    a["condition"]["track"] = b["condition"]["track"] = "controlled_capability"
    add(ledger, "c", a)
    add(ledger, "d", b)
    with pytest.raises(LedgerError, match="known matched"):
        comparison(ledger, ["c"], ["d"])


def test_checkpoint_clock_regression_and_terminal_evidence_loss(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    value = frozen(bundle)
    ledger.start("a", value, attempt_id="a1", origin="synthetic")
    event = {"category": "runtime", "code": "progress", "source": "fixture"}
    ledger.checkpoint("a", "a1", event_id="1", event=event,
                      timing={"end_to_end": elapsed(8, coverage="partial")}, artifacts=[])
    with pytest.raises(LedgerError, match="decreased"):
        ledger.checkpoint("a", "a1", event_id="2", event=event,
                          timing={"end_to_end": elapsed(7, coverage="partial")}, artifacts=[])
    terminal = result(value)
    with pytest.raises(LedgerError, match="retain checkpoint"):
        ledger.finalize("a", terminal)
    terminal["attempts"][0]["events"] = [event]
    terminal["attempts"][0]["timing"] = {}
    terminal["attempts"][0].pop("time_to_verified_completion")
    with pytest.raises(LedgerError, match="discarded"):
        ledger.finalize("a", terminal)


def test_concurrent_identical_starts_append_once(tmp_path, bundle):
    path, value = tmp_path / "ledger.jsonl", frozen(bundle)
    with ThreadPoolExecutor(max_workers=4) as pool:
        writes = list(pool.map(lambda _: Ledger(path).start(
            "t", value, attempt_id="a1", origin="synthetic"), range(8)))
    assert sum(writes) == 1
    assert len(Ledger(path).snapshot()["t"]["starts"]) == 1


@pytest.mark.parametrize("field,value", [("attempt_id", "absent"), ("passed", True),
                                       ("total", 0), ("passed", 4), ("artifacts", [])])
def test_auxiliary_counts_reject_unbound_or_invalid_evidence(tmp_path, bundle, field, value):
    ledger, frozen_value = Ledger(tmp_path / "ledger.jsonl"), frozen(bundle)
    ledger.start("t", frozen_value, attempt_id="a1", origin="synthetic")
    terminal = result(frozen_value, stop="agent_finished")
    partial = {"result": manifest_reference(terminal), "attempt_id": "a1", "passed": 2,
               "total": 3, "source": "fixture", "artifacts": [{"uri": "synthetic:counts", "sha256": "f" * 64}]}
    partial[field] = value
    with pytest.raises(LedgerError):
        ledger.finalize("t", terminal, partial=partial)
    assert ledger.snapshot()["t"]["attempts"] == []


def test_explicit_configuration_factor_not_arbitrary_pooling(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    a, b = frozen(bundle), frozen(bundle)
    b["agent"]["configuration"] = known({"variant": "compact"})
    b["condition"]["agent"] = manifest_reference(b["agent"])
    add(ledger, "a", a)
    add(ledger, "b", b)
    report = compare(ledger, cohorts={"baseline": ["a"], "compact": ["b"]},
                     suite=[manifest_reference(a["task"])], factor="agent_configuration")
    assert report["both_success_complete_time_subset"]["paired_denominator"] == 1
    with pytest.raises(LedgerError, match="duplicate"):
        comparison(ledger, ["a"], ["a"])
    with pytest.raises(LedgerError, match="ineligible"):
        comparison(ledger, ["a"], ["b"], suite=[{**manifest_reference(a["task"]), "sha256": "0" * 64}])


@pytest.mark.parametrize("field", ["source", "reason"])
@pytest.mark.parametrize("nested", [False, True])
def test_configuration_payload_keys_remain_controlled_unless_explicit_factor(tmp_path, bundle, field, nested):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    a, b = frozen(bundle), frozen(bundle)
    for value, instructions in ((a, "instructions-A.md"), (b, "instructions-B.md")):
        payload = {field: instructions}
        if nested:
            payload = {"nested": payload}
        value["agent"]["configuration"] = known(payload)
        value["condition"]["agent"] = manifest_reference(value["agent"])
    add(ledger, "a", a)
    add(ledger, "b", b)
    kwargs = dict(cohorts={"A": ["a"], "B": ["b"]}, suite=[manifest_reference(a["task"])])
    with pytest.raises(LedgerError, match="incompatible"):
        compare(ledger, **kwargs, factor="target")
    report = compare(ledger, **kwargs, factor="agent_configuration")
    assert report["both_success_complete_time_subset"]["paired_denominator"] == 1
    assert report["disclosures"][0]["bundle"]["agent"]["configuration"] == a["agent"]["configuration"]


def usage_declaration(trial_id, terminal, metric, quantity, unit):
    return {"trial_id": trial_id, "attempt_id": terminal["attempts"][-1]["id"],
            "result": manifest_reference(terminal), "metric": metric,
            "quantity": quantity, "unit": unit, "source": "synthetic-unit-receipt"}


@pytest.mark.parametrize("metric,quantity,unit", [
    ("cpu_power_watts", "gauge", "watts"), ("rail_watts", "gauge", "watts"),
    ("tokens_per_second", "rate", "tokens/second"), ("price", "unit_price", "USD/token"),
])
def test_nonliteral_power_rates_and_unit_prices_never_sum(tmp_path, bundle, metric, quantity, unit):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    declarations, suite = [], []
    for task in ("t1", "t2"):
        for label in ("A", "B"):
            value = frozen(bundle, task=task, target="model-" + label)
            terminal = result(value)
            terminal["attempts"][0]["usage"][metric] = known(3.5)
            trial_id = task + label
            ledger.start(trial_id, value, attempt_id="a1", origin="synthetic")
            ledger.finalize(trial_id, terminal)
            declarations.append(usage_declaration(trial_id, terminal, metric, quantity, unit))
        suite.append(manifest_reference(value["task"]))
    before = ledger.snapshot()
    for declared in (None, declarations):
        report = compare(ledger, cohorts={"A": ["t1A", "t2A"], "B": ["t1B", "t2B"]},
                         suite=suite, usage_declarations=declared)
        summary = report["cohorts"]["A"]["usage"][metric]
        assert summary["total"] is None and summary["observed_sum"] is None
        assert summary["complete"] == 2 and summary["denominator"] == 2
        assert report["cohorts"]["A"]["attempts"][0]["attempt"]["usage"][metric] == known(3.5)
    assert ledger.snapshot() == before


def test_additive_usage_requires_consistent_bound_semantics_for_every_known_value(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    declarations, suite = [], []
    for task in ("t1", "t2"):
        for label in ("A", "B"):
            value = frozen(bundle, task=task, target="model-" + label)
            terminal = result(value, stop="success" if task == "t1" else "timeout")
            terminal["attempts"][0]["usage"].update(spend=known(2.5), tokens=known(10))
            trial_id = task + label
            ledger.start(trial_id, value, attempt_id="a1", origin="synthetic")
            ledger.finalize(trial_id, terminal)
            declarations.extend([usage_declaration(trial_id, terminal, "spend", "total_spend", "USD"),
                                 usage_declaration(trial_id, terminal, "tokens", "count", "tokens")])
        suite.append(manifest_reference(value["task"]))
    kwargs = dict(cohorts={"A": ["t1A", "t2A"], "B": ["t1B", "t2B"]}, suite=suite)
    report = compare(ledger, **kwargs, usage_declarations=declarations)
    assert report["cohorts"]["A"]["usage"]["spend"]["total"] == 5
    assert report["cohorts"]["A"]["usage"]["tokens"]["total"] == 20
    assert report["cohorts"]["A"]["usage"]["price"]["total"] is None
    missing = compare(ledger, **kwargs, usage_declarations=declarations[1:])
    assert missing["cohorts"]["A"]["usage"]["spend"]["total"] is None
    assert missing["cohorts"]["A"]["usage"]["spend"]["observed_sum"] is None
    assert missing["cohorts"]["A"]["usage"]["spend"]["aggregation"] == "missing_semantics"
    for change in ("currency", "missing_unit", "watts", "binding"):
        invalid = deepcopy(declarations)
        if change == "currency":
            invalid[0]["unit"] = "EUR"
        elif change == "missing_unit":
            invalid[0].pop("unit")
        elif change == "watts":
            invalid[0].update(quantity="energy", unit="watts")
        else:
            invalid[0]["result"]["sha256"] = "0" * 64
        with pytest.raises(LedgerError):
            compare(ledger, **kwargs, usage_declarations=invalid)


def test_count_semantics_reject_fractional_evidence(tmp_path, bundle):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    a, b = frozen(bundle), frozen(bundle, target="model-B")
    terminal = result(a)
    terminal["attempts"][0]["usage"]["price"] = known(2.5)
    ledger.start("a", a, attempt_id="a1", origin="synthetic")
    ledger.finalize("a", terminal)
    add(ledger, "b", b)
    declaration = usage_declaration("a", terminal, "price", "count", "credits")
    with pytest.raises(LedgerError, match="integer evidence"):
        compare(ledger, cohorts={"A": ["a"], "B": ["b"]}, suite=[manifest_reference(a["task"])],
                usage_declarations=[declaration])
