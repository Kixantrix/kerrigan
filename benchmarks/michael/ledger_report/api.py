"""Offline Linux filesystem ledger and explicit comparisons; never executes tools."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re

from benchmarks.michael.contracts.manifests import manifest_reference, validate_bundle


class LedgerError(ValueError):
    """Invalid, conflicting, or corrupt ledger/report evidence."""


def _json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise LedgerError(f"invalid JSON evidence: {exc}") from exc


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise LedgerError("expected nonempty identifier/source")
    return value


def _fields(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise LedgerError(f"expected fields {sorted(required)}; optional {sorted(optional)}")


def _ref(value, artifact=False):
    _fields(value, {"uri", "sha256"} if artifact else {"id", "revision", "sha256"})
    for key in value:
        _text(value[key])
    if not re.fullmatch("[0-9a-f]{64}", value["sha256"]):
        raise LedgerError("reference requires lowercase SHA-256")


def _unknown():
    return {"status": "unknown", "source": "ledger", "reason": "not measured"}


def _result(bundle, attempts):
    return {"schema_version": 1, "kind": "result", "id": "ledger-recovery",
            "revision": "1", "provenance": {"source_id": "ledger interrupted recovery"},
            "condition": manifest_reference(bundle["condition"]), "attempts": attempts}


def _interrupted(attempt_id, retry_of, events, timing):
    return {"id": attempt_id, **({"retry_of": retry_of} if retry_of else {}),
            "verdict": "ungraded", "state": "interrupted", "stop_reason": "interruption",
            "verifier": {"status": "not_run", "independent": False, "source": "ledger recovery"},
            "events": events, "timing": timing, "usage": {},
            "time_to_verified_completion": _unknown()}


def _partial(value, result):
    _fields(value, {"result", "attempt_id", "passed", "total", "source", "artifacts"})
    if value["result"] != manifest_reference(result):
        raise LedgerError("partial evidence must bind exact result reference")
    if value["attempt_id"] != result["attempts"][-1]["id"]:
        raise LedgerError("partial evidence must bind current attempt")
    _text(value["source"])
    if any(type(value[k]) is not int or value[k] < 0 for k in ("passed", "total")):
        raise LedgerError("partial assertions require nonnegative integer counts")
    if value["total"] < 1 or value["passed"] > value["total"]:
        raise LedgerError("partial assertion denominator must be positive and cover passes")
    if not isinstance(value["artifacts"], list) or not value["artifacts"]:
        raise LedgerError("partial assertions require artifact references")
    for artifact in value["artifacts"]:
        _ref(artifact, artifact=True)


def _apply(state, record):
    if not isinstance(record, dict):
        raise LedgerError("ledger record must be an object")
    kind = record.get("kind")
    if kind == "start":
        _fields(record, {"kind", "trial_id", "attempt_id", "bundle", "origin"}, {"retry_of"})
        trial_id, attempt_id = _text(record["trial_id"]), _text(record["attempt_id"])
        if record["origin"] not in {"synthetic", "new_trial"}:
            raise LedgerError("start origin must be synthetic or new_trial; historical imports are separate")
        bundle = validate_bundle(**record["bundle"])
        if "result" in bundle:
            raise LedgerError("start must freeze a bundle without a result")
        trial = state.get(trial_id)
        if trial is None:
            if "retry_of" in record:
                raise LedgerError("first attempt cannot retry absent evidence")
            trial = state[trial_id] = {"bundle": bundle, "origin": record["origin"], "attempts": [],
                                      "starts": [], "checkpoints": [], "terminals": []}
        else:
            condition = bundle["condition"]
            if bundle != trial["bundle"] or record["origin"] != trial["origin"]:
                raise LedgerError("conflicting frozen start")
            if len(trial["attempts"]) != len(trial["starts"]):
                raise LedgerError("prior attempt must terminate before retry")
            if record.get("retry_of") not in {a["id"] for a in trial["attempts"]}:
                raise LedgerError("retry must reference a prior retained attempt")
            if condition["retry_policy"] != "declared_retries":
                raise LedgerError("retry not declared by frozen policy")
            limit = condition["budgets"]["attempt_limit"]
            if limit["status"] == "known" and len(trial["starts"]) >= limit["value"]:
                raise LedgerError("declared attempt limit exceeded")
        if attempt_id in {s["attempt_id"] for s in trial["starts"]}:
            raise LedgerError("duplicate attempt start")
        trial["starts"].append(record)
        return
    if kind not in {"checkpoint", "terminal"}:
        raise LedgerError("unsupported ledger record kind")
    trial = state.get(record.get("trial_id"))
    if trial is None:
        raise LedgerError("validated frozen start required")
    start = trial["starts"][-1]
    active = len(trial["starts"]) > len(trial["attempts"])
    if not active:
        raise LedgerError("attempt already terminal")
    if kind == "checkpoint":
        _fields(record, {"kind", "trial_id", "attempt_id", "event_id", "event", "timing", "artifacts"})
        if record["attempt_id"] != start["attempt_id"]:
            raise LedgerError("checkpoint must reference active attempt")
        _text(record["event_id"])
        if any(c["event_id"] == record["event_id"] for c in trial["checkpoints"]):
            raise LedgerError("conflicting event identifier")
        if not isinstance(record["artifacts"], list):
            raise LedgerError("artifacts must be an array")
        for artifact in record["artifacts"]:
            _ref(artifact, artifact=True)
        attempt = _interrupted(start["attempt_id"], start.get("retry_of"),
                               [record["event"]], record["timing"])
        validate_bundle(**trial["bundle"], result=_result(trial["bundle"], [attempt] if not start.get("retry_of")
                        else trial["attempts"] + [attempt]))
        prior = _observed(trial)[1]
        _retains_timing(prior, record["timing"], checkpoint=True)
        trial["checkpoints"].append(record)
    else:
        _fields(record, {"kind", "trial_id", "result", "partial"})
        result = validate_bundle(**trial["bundle"], result=record["result"])["result"]
        attempts = result["attempts"]
        if attempts[:-1] != trial["attempts"] or len(attempts) != len(trial["starts"]):
            raise LedgerError("terminal must retain every prior attempt unchanged")
        attempt = attempts[-1]
        if attempt["id"] != start["attempt_id"] or attempt.get("retry_of") != start.get("retry_of"):
            raise LedgerError("terminal must bind active attempt and retry")
        events, timing = _observed(trial)
        if attempt["events"][:len(events)] != events:
            raise LedgerError("terminal must retain checkpoint events")
        _retains_timing(timing, attempt["timing"])
        if record["partial"] is not None:
            _partial(record["partial"], result)
        trial["attempts"] = attempts
        trial["terminals"].append(record)


def _retains_timing(prior, current, checkpoint=False):
    for phase, evidence in prior.items():
        if evidence["status"] != "known":
            continue
        new = current.get(phase)
        if new is None and checkpoint:
            continue
        if new is None or new["status"] != "known":
            raise LedgerError("observed timing cannot be discarded")
        old, latest = evidence["value"], new["value"]
        if any(old.get(k) != latest.get(k) for k in ("clock", "host_ids", "correlation_id")):
            raise LedgerError("timing clock provenance changed")
        if latest["seconds"] < old["seconds"]:
            raise LedgerError("observed elapsed time decreased")


def _observed(trial):
    events, timing = [], {}
    for checkpoint in trial["checkpoints"]:
        if checkpoint["attempt_id"] == trial["starts"][-1]["attempt_id"]:
            events.append(checkpoint["event"])
            timing.update(checkpoint["timing"])
    return events, timing


class Ledger:
    """Append/fsync hash-chained JSONL under an advisory Linux file lock.

    Own the ledger path exclusively; this is durability, not adversarial isolation.
    A torn append is an explicit error, never silently truncated or repaired.
    """

    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def _locked(self):
        try:
            with self.path.open("a+b") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX)
                fd = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
                yield stream
        except OSError as exc:
            raise LedgerError(f"ledger filesystem error at {self.path}: {exc}") from exc

    def _read(self, stream):
        def pairs(items):
            value = {}
            for key, child in items:
                if key in value:
                    raise LedgerError(f"duplicate JSON key: {key}")
                value[key] = child
            return value

        stream.seek(0)
        state, records, previous = {}, [], None
        for index, line in enumerate(stream, 1):
            if not line.endswith(b"\n"):
                raise LedgerError(f"truncated ledger line {index}")
            try:
                envelope = json.loads(line, object_pairs_hook=pairs)
                _fields(envelope, {"sequence", "previous", "record", "sha256"})
                body = {key: envelope[key] for key in ("sequence", "previous", "record")}
                if type(envelope["sequence"]) is not int or envelope["sequence"] != index:
                    raise LedgerError("ledger sequence mismatch")
                if envelope["previous"] != previous or hashlib.sha256(_json(body)).hexdigest() != envelope["sha256"]:
                    raise LedgerError("ledger hash chain mismatch")
                _apply(state, envelope["record"])
            except (ValueError, TypeError, KeyError, RecursionError) as exc:
                raise LedgerError(f"corrupt ledger line {index}: {exc}") from exc
            records.append(envelope["record"])
            previous = envelope["sha256"]
        return state, records, previous

    def _append(self, record):
        record = deepcopy(record)
        _json(record)
        with self._locked() as stream:
            state, records, previous = self._read(stream)
            if record in records:
                return False
            _apply(state, record)
            body = {"sequence": len(records) + 1, "previous": previous, "record": record}
            envelope = {**body, "sha256": hashlib.sha256(_json(body)).hexdigest()}
            stream.seek(0, os.SEEK_END)
            stream.write(_json(envelope) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        return True

    def start(self, trial_id, bundle, *, attempt_id, origin, retry_of=None):
        return self._append({"kind": "start", "trial_id": trial_id, "bundle": bundle,
                             "attempt_id": attempt_id, "origin": origin,
                             **({"retry_of": retry_of} if retry_of is not None else {})})

    def checkpoint(self, trial_id, attempt_id, *, event_id, event, timing, artifacts):
        return self._append(dict(kind="checkpoint", trial_id=trial_id, attempt_id=attempt_id,
                                 event_id=event_id, event=event, timing=timing, artifacts=artifacts))

    def finalize(self, trial_id, result, *, partial=None):
        return self._append(dict(kind="terminal", trial_id=trial_id, result=result, partial=partial))

    def snapshot(self):
        with self._locked() as stream:
            return self._read(stream)[0]

    def recover(self, trial_id):
        """Explicit interrupted terminal; preserves elapsed coverage, never runs tools."""
        trial = self.snapshot().get(trial_id)
        if trial is None:
            raise LedgerError("cannot recover absent start")
        if len(trial["attempts"]) == len(trial["starts"]):
            if trial["attempts"][-1]["state"] == "interrupted":
                return False
            raise LedgerError("cannot recover already terminal attempt")
        start = trial["starts"][-1]
        events, timing = _observed(trial)
        end = timing.get("end_to_end", _unknown())
        if end["status"] == "known":
            end["value"]["coverage"] = "partial"
        attempt = _interrupted(start["attempt_id"], start.get("retry_of"), events, timing)
        return self.finalize(trial_id, _result(trial["bundle"], trial["attempts"] + [attempt]))


def _success(attempt):
    return (attempt["verdict"] == "passed" and attempt["state"] == "completed"
            and attempt["stop_reason"] == "success" and attempt["verifier"]["independent"])


def _semantic(value):
    if isinstance(value, dict):
        if (value.get("status") in {"known", "unknown", "unsupported", "not_applicable"}
                and "source" in value and not value.keys() - {"status", "source", "reason", "value"}):
            return {k: deepcopy(v) for k, v in value.items() if k not in {"source", "reason"}}
        return {k: deepcopy(v) if k == "provenance" else _semantic(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_semantic(v) for v in value]
    return value


def _aggregate(evidence, timing=False, additive=True):
    complete, partial, known_sum, statuses = 0, 0, 0, {}
    for item in evidence:
        statuses[item["status"]] = statuses.get(item["status"], 0) + 1
        if item["status"] == "known":
            value = item["value"]
            if additive:
                known_sum += value["seconds"] if timing else value
            if timing and value["coverage"] == "partial":
                partial += 1
            else:
                complete += 1
    return {"denominator": len(evidence), "complete": complete, "partial": partial,
            "statuses": statuses, "observed_sum": known_sum if additive and complete + partial else None,
            "total": known_sum if additive and evidence and complete == len(evidence) else None}


_ADDITIVE_UNITS = {"count": {"tokens", "credits", "calls", "bytes"},
                   "total_spend": {"USD", "EUR", "GBP"},
                   "energy": {"joules", "watt_hours"}}


def _usage_semantics(state, selected_ids, declarations):
    if not isinstance(declarations, list):
        raise LedgerError("usage declarations must be an array")
    bound, consistent = {}, {}
    for declaration in declarations:
        _fields(declaration, {"trial_id", "attempt_id", "result", "metric", "quantity", "unit", "source"})
        for field in ("trial_id", "attempt_id", "metric", "quantity", "unit", "source"):
            _text(declaration[field])
        _ref(declaration["result"])
        trial_id, attempt_id, metric = (declaration[k] for k in ("trial_id", "attempt_id", "metric"))
        if trial_id not in selected_ids:
            raise LedgerError("usage declaration must bind a selected trial")
        terminal = next((t for t in state[trial_id]["terminals"]
                         if t["result"]["attempts"][-1]["id"] == attempt_id), None)
        if terminal is None or declaration["result"] != manifest_reference(terminal["result"]):
            raise LedgerError("usage declaration must bind exact terminal result/current attempt")
        usage = terminal["result"]["attempts"][-1]["usage"]
        if metric not in usage:
            raise LedgerError("usage declaration references absent metric")
        quantity, unit = declaration["quantity"], declaration["unit"]
        if quantity not in {*_ADDITIVE_UNITS, "gauge", "rate", "unit_price"}:
            raise LedgerError("unsupported usage quantity")
        if quantity in _ADDITIVE_UNITS and unit not in _ADDITIVE_UNITS[quantity]:
            raise LedgerError("unsupported additive quantity/unit pair")
        if quantity == "count" and usage[metric]["status"] == "known" and type(usage[metric]["value"]) is not int:
            raise LedgerError("count quantity requires integer evidence")
        key = (trial_id, attempt_id, metric)
        if key in bound:
            raise LedgerError("duplicate usage declaration")
        semantics = (quantity, unit)
        if metric in consistent and consistent[metric] != semantics:
            raise LedgerError("inconsistent usage quantity/unit semantics across comparison")
        consistent[metric] = semantics
        bound[key] = declaration
    return bound


def _usage_aggregate(attempts, metric, semantics):
    evidence = [a["attempt"]["usage"].get(metric, _unknown()) for a in attempts]
    declarations = [semantics.get((a["trial_id"], a["attempt"]["id"], metric)) for a in attempts]
    measured = [d for d, e in zip(declarations, evidence) if e["status"] == "known"]
    declared = [d for d in declarations if d is not None]
    quantity = declared[0]["quantity"] if declared else None
    additive = bool(measured) and all(d is not None for d in measured) and quantity in _ADDITIVE_UNITS
    summary = _aggregate(evidence, additive=additive)
    summary.update(declarations=deepcopy(declared), quantity=quantity,
                   unit=declared[0]["unit"] if declared else None,
                   aggregation="additive" if additive else "nonadditive" if quantity in {
                       "gauge", "rate", "unit_price"} else "missing_semantics")
    return summary


def compare(ledger, *, cohorts, suite, factor="target", usage_declarations=None):
    """Compare named cohorts against one explicit frozen eligible suite; no rankings.

    A trial owns all retries. At most one trial per task per cohort. Only the
    target, or configuration (not harness), may be the declared varying factor.
    """
    if factor not in {"target", "agent_configuration"}:
        raise LedgerError("unsupported intended comparison factor")
    if not isinstance(cohorts, dict) or len(cohorts) != 2 or not isinstance(suite, list) or not suite:
        raise LedgerError("comparison requires two explicit cohorts and nonempty frozen suite")
    for reference in suite:
        _ref(reference)
    keys = [r["sha256"] for r in suite]
    if len(set(keys)) != len(keys) or len({r["id"] for r in suite}) != len(suite):
        raise LedgerError("duplicate eligible task")
    state, selected, used, baseline, within = ledger.snapshot(), {}, set(), None, {}
    disclosures = []
    for label, trial_ids in cohorts.items():
        _text(label)
        if not isinstance(trial_ids, list) or not trial_ids:
            raise LedgerError("cohort must name started trials explicitly")
        selected[label] = {}
        for trial_id in trial_ids:
            _text(trial_id)
            if trial_id in used or trial_id not in state:
                raise LedgerError("duplicate or missing trial in cohorts")
            used.add(trial_id)
            trial = state[trial_id]
            bundle, condition = trial["bundle"], trial["bundle"]["condition"]
            reference = manifest_reference(bundle["task"])
            if reference not in suite or reference["sha256"] in selected[label]:
                raise LedgerError("ineligible or duplicate cohort task")
            selected[label][reference["sha256"]] = (trial_id, trial)
            common = {"origin": trial["origin"], "harness": bundle["agent"]["harness"],
                      **{k: condition[k] for k in ("track", "budgets", "cache_policy",
                         "retry_policy", "capabilities", "required_semantics")}}
            if factor == "target":
                common["configuration"] = bundle["agent"]["configuration"]
            else:
                common["target"] = bundle["target"]
            if condition["track"] != "practical_system":
                common.update(hosts=condition["hosts"], observability=condition["observability"])
                if factor == "target":
                    common["runtime"] = bundle["target"]["runtime"]
                controls = [bundle["agent"]["configuration"], condition["cache_policy"],
                            *condition["budgets"].values(), *condition["hosts"].values()]
                if any(e["status"] != "known" for e in controls):
                    raise LedgerError("controlled comparison requires known matched controls")
            signature = _semantic(common)
            if baseline is None:
                baseline = signature
            elif signature != baseline:
                raise LedgerError("incompatible task/harness/policy/controlled conditions")
            varying = _semantic(bundle["target"] if factor == "target" else bundle["agent"]["configuration"])
            if label in within and varying != within[label]:
                raise LedgerError("intended factor changes within cohort")
            within[label] = varying
            disclosures.append({"cohort": label, "trial_id": trial_id, "bundle": bundle,
                                "origin": trial["origin"]})
    semantics = _usage_semantics(state, used, [] if usage_declarations is None else usage_declarations)
    reports, rows, differences = {}, [], []
    for label, trials in selected.items():
        attempts, first, eventual = [], 0, 0
        for trial_id, trial in trials.values():
            retained = deepcopy(trial["attempts"])
            if len(retained) < len(trial["starts"]):
                start = trial["starts"][-1]
                events, timing = _observed(trial)
                end = timing.get("end_to_end", _unknown())
                if end["status"] == "known":
                    end["value"]["coverage"] = "partial"
                pending = _interrupted(start["attempt_id"], start.get("retry_of"), events, timing)
                pending["state"] = "unfinished"
                pending["stop_reason"] = "not_terminal"
                retained.append(pending)
            first += int(_success(retained[0]))
            eventual += int(any(_success(a) for a in retained))
            for attempt in retained:
                attempts.append({"trial_id": trial_id, "attempt": attempt,
                                 "partial": next((t["partial"] for t in trial["terminals"]
                                                 if t["result"]["attempts"][-1]["id"] == attempt["id"]), None)})
        raw = [a["attempt"] for a in attempts]
        phases = {p: _aggregate([a["timing"].get(p, _unknown()) for a in raw], True)
                  for p in ("queue", "provisioning", "setup", "agent_work", "verification", "end_to_end")}
        usage = {k: _usage_aggregate(attempts, k, semantics)
                 for k in {"price", "credits", "power", *(k for a in raw for k in a["usage"])}}
        partials = [a["partial"] for a in attempts if a["partial"] is not None]
        reports[label] = {"eligible_tasks": len(suite), "started_trials": len(trials),
                          "started_attempts": len(raw), "first_attempt_verified": first,
                          "eventual_verified": eventual, "completion_coverage": eventual / len(suite),
                          "attempts": attempts, "phases": phases, "usage": usage,
                          "trial_evidence": {trial_id: trial for trial_id, trial in trials.values()},
                          "completion_timing": _aggregate([
                              a.get("time_to_verified_completion", _unknown()) for a in raw if _success(a)], True),
                          "partial_assertions": {"attempt_denominator": len(raw),
                                                 "measured_attempts": len(partials),
                                                 "observed_passed": sum(p["passed"] for p in partials),
                                                 "observed_total": sum(p["total"] for p in partials)},
                          "verifier_statuses": {v: sum(a["verifier"]["status"] == v for a in raw)
                                                for v in ("passed", "failed", "not_run", "error")},
                          "independently_verified_attempts": sum(
                              a["verifier"]["independent"] and a["verifier"]["status"] in {"passed", "failed"}
                              for a in raw),
                          "states": {s: sum(a["state"] == s for a in raw)
                                     for s in ("completed", "stopped", "interrupted", "unfinished")},
                          "stops": {s: sum(a["stop_reason"] == s for a in raw)
                                    for s in sorted({a["stop_reason"] for a in raw})},
                          "outcomes": {v: sum(a["verdict"] == v for a in raw)
                                       for v in ("passed", "failed", "ungraded")},
                          "all_attempt_seconds_per_verified_task":
                              phases["end_to_end"]["total"] / eventual
                              if eventual and phases["end_to_end"]["total"] is not None else None}
    for reference in suite:
        row = {"task": reference}
        times = []
        for label in cohorts:
            item = selected[label].get(reference["sha256"])
            successes = [a["attempt"] for a in reports[label]["attempts"]
                         if item and a["trial_id"] == item[0] and _success(a["attempt"])]
            completion = successes[0].get("time_to_verified_completion", _unknown()) if successes else _unknown()
            row[label] = {"trial_id": item[0] if item else None,
                          "verified": bool(successes), "completion_time": completion,
                          "completion_time_scope": "successful_attempt_end_to_end",
                          "completion_attempt_id": successes[0]["id"] if successes else None,
                          "attempt_evidence": [a for a in reports[label]["attempts"]
                                               if item and a["trial_id"] == item[0]],
                          "attempt_ids": [s["attempt_id"] for s in item[1]["starts"]] if item else []}
            times.append(completion["value"]["seconds"] if completion["status"] == "known" else None)
        if all(t is not None for t in times):
            differences.append({"task": reference, "second_minus_first_seconds": times[1] - times[0]})
        rows.append(row)
    return {"factor": factor, "cohort_order": list(cohorts), "cohorts": reports, "paired_tasks": rows,
            "both_success_complete_time_subset": {"eligible_denominator": len(suite),
                                                  "paired_denominator": len(differences),
                                                  "differences": differences},
            "disclosures": disclosures,
            "boundaries": "Synthetic/new-trial classes never pool; declarations are not execution, identity, "
                          "isolation, price, or power attestations. No universal ranking or inferred superiority."}
