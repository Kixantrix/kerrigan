"""Generate condition-separated targets from verified ledger-derived records."""
import argparse
from collections import Counter
import difflib
import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from statistics import median
from math import isfinite

from benchmarks.michael.curriculum.metrics import wilson
from benchmarks.michael.replay_grader import specs
from benchmarks.michael.tasks import curriculum
from benchmarks.michael.ledger_report.api import Ledger
from benchmarks.michael.replay_trial.validator import digest as condition_digest

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CLASSES = ("cloud", "local laptop", "self-hosted infrastructure")
FAMILIES = {"validator": "Implement", "grouping": "Implement", "status": "Implement",
            "selfhost-redeploy-state": "Operate", "sr-temporal-assay": "Experiment"}
FAILURE_MODES = ("unsupported-defect-claim", "claimed-fix-not-implemented", "sandbox-boundary-write",
                 "harness-cap", "task-caused", "contention-timeout", "model-failure-unclassified",
                 "harness-error", "invented-path-read")


def failure_modes(attribution):
    """Map attribution evidence, never primary-selection boilerplate, to stable labels."""
    cause = attribution.get("cause")
    if cause == "task":
        return ["task-caused"]
    if attribution.get("outcome") == "contention-timeout":
        return ["contention-timeout"]
    if cause == "harness":
        reason = attribution.get("nativeStop", "")
        return ["harness-cap" if any(word in reason for word in ("cap", "budget", "overflow")) else "harness-error"]
    evidence = [attribution.get("deterministicEvidence", "")]
    evidence.extend(item if isinstance(item, str) else item.get("description", "")
        for verdict in attribution.get("verdicts", []) for item in verdict.get("evidence", []))
    text = "\n".join(evidence)
    modes = []
    if "claimFixed=false" in text:
        modes.append("claimed-fix-not-implemented")
    if "glob-overlap" in text and any(word in text.lower() for word in (
            "did not contribute", "did not cause", "non-contributing", "false-positive", "false positives")):
        modes.append("unsupported-defect-claim")
    if "auth-bypass" in text and any(word in text.lower() for word in ("absent", "unsupported", "no authentication")):
        modes.append("unsupported-defect-claim")
    if ("$TMPDIR" in text and "outside" in text) or "out-of-scope write" in text:
        modes.append("sandbox-boundary-write")
    return modes or ["model-failure-unclassified"]


def size(task):
    if task in curriculum.PACKAGES:
        measured = curriculum.task_size(task)
        touched = measured["oracle_files_changed"]
        changed = measured["oracle_lines_added"] + measured["oracle_lines_removed"]
        tier = "small" if touched <= 1 and changed <= 100 else (
            "medium" if touched <= 4 and changed <= 400 else "large")
        return {"tier": tier, **measured}
    agent, _, _, _ = specs.package(task)
    reference = specs.unbundle(task, specs.reference(task))
    touched = 0
    changed = 0
    for name, data in reference.items():
        before = agent[name].decode().splitlines()
        after = data.decode().splitlines()
        if before != after:
            touched += 1
        diff = list(difflib.unified_diff(before, after, n=0))
        changed += sum(line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
                       for line in diff)
    tier = "small" if touched <= 1 and changed <= 100 else (
        "medium" if touched <= 4 and changed <= 400 else "large")
    return {"tier": tier, "oracle_files_touched": touched, "oracle_lines_changed": changed,
            "files_to_read": len(agent), "checks": sum(specs.spec(task)["denominators"].values())}


def archived_ledgers(data, path, selected, decisions=()):
    with path.open("rb") as stream:
        archive_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    if archive_sha != data["archiveSha256"]:
        raise ValueError("matrix evidence archive mismatch")
    found = {}
    selected = set(selected) | set(decisions)
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            if member.name not in selected:
                continue
            if not member.isfile() or member.name in found or member.size > 1048576:
                raise ValueError("invalid archived matrix ledger")
            raw = archive.extractfile(member).read()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != data["members"][member.name]:
                raise ValueError("matrix archived ledger mismatch")
            if member.name in decisions:
                found[member.name] = json.loads(raw)
            else:
                state, _, head = Ledger(member.name)._read(io.BytesIO(raw))
                found[member.name] = (state, digest, head)
    if set(found) != set(selected):
        raise ValueError("missing archived matrix ledger")
    return found, archive_sha


def seed():
    records = []
    sources = []
    for filename, label in (("MB-009r-verification.json", "v1"), ("MB-010r-verification.json", "v2")):
        path = ROOT / "benchmarks/michael/curriculum" / filename
        raw = path.read_bytes()
        data = json.loads(raw)
        sources.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest(),
                        "role": "sealed primary-selection and native-measurement index"})
        tasks = data["models"] if label == "v1" else data["primaryModels"]
        classifications = data.get("attemptClassifications", [])
        decision_paths = {}
        for row in classifications:
            if row["status"] == "pass":
                continue
            prefix = row["attemptRoot"].replace("/trials/", "/attribution/") + "/" + row["model"]
            matches = [prefix + "/" + name for name in ("decision.json", "attribution.json")
                       if prefix + "/" + name in data["members"]]
            if matches:
                decision_paths[row["task"], row["model"], row["attemptRoot"]] = matches[0]
        selections = {}
        for task, targets in tasks.items():
            for model, value in targets.items():
                candidates = [p for p in data["members"] if p.endswith(f"/trials/{task}/ledger.jsonl")]
                selected = value.get("attemptRoot", "")
                if selected:
                    candidates = [selected + "/ledger.jsonl"]
                if len(candidates) != 1:
                    raise ValueError("ambiguous primary matrix ledger")
                selections[task, model] = candidates[0]
        archive_path = path.with_name(filename.replace("-verification.json", "-evidence.tar.gz"))
        ledgers, archive_sha = archived_ledgers(data, archive_path, set(selections.values()),
                                              set(decision_paths.values()))
        sources.append({"path": str(archive_path.relative_to(ROOT)), "sha256": archive_sha,
                        "role": "sealed ledger bytes; hash chain and frozen bundles validated",
                        "prior_attempts": [{"task": row["task"], "model": row["model"], "round": label,
                            "status": row["status"], "failure_modes": failure_modes(
                                {**ledgers[decision_paths[row["task"], row["model"], row["attemptRoot"]]],
                                 "cause": row["cause"],
                                 **({"nativeStop": row["reason"]} if row["cause"] == "harness" else {})}),
                            "provenance": {"decision": decision_paths[row["task"], row["model"], row["attemptRoot"]],
                                "sha256": data["members"][decision_paths[row["task"], row["model"], row["attemptRoot"]]],
                                "classification_reason": row["reason"]}}
                            for row in classifications if not row["primary"] and
                            (row["task"], row["model"], row["attemptRoot"]) in decision_paths]})
        for task, targets in tasks.items():
            dimensions = size(task)
            for model, value in targets.items():
                ledger_path = selections[task, model]
                states, ledger_sha, head = ledgers[ledger_path]
                trial = states[model]
                if len(trial["starts"]) != 1 or len(trial["attempts"]) != 1 or trial["origin"] != "new_trial":
                    raise ValueError("matrix seed requires one observed primary attempt")
                frozen = trial["bundle"]["agent"]["configuration"]["value"]
                if condition_digest(frozen) != value["conditionSha256"]:
                    raise ValueError("matrix frozen condition mismatch")
                attempt = trial["attempts"][0]
                passed = attempt["verdict"] == "passed"
                timing = attempt["time_to_verified_completion"]
                seconds = timing["value"]["seconds"] if passed and timing["status"] == "known" else None
                if passed != (value["completionSeconds"] is not None) or seconds != value["completionSeconds"]:
                    raise ValueError("matrix ledger/selection result mismatch")
                failure = []
                if not passed:
                    decision = decision_paths.get((task, model, ledger_path.removesuffix("/ledger.jsonl")))
                    failure = failure_modes(ledgers[decision]) if decision else ["model-failure-unclassified"]
                records.append({
                    "task": task, "repeat": 1, "model": model, "deployment_class": "cloud",
                    "condition": data["condition"], "tool_host": "local macOS MXC",
                    "round": label, "family": FAMILIES.get(task) or curriculum.meta(task)["family"],
                    "size": dimensions, "resolved": passed, "completion_seconds": seconds,
                    "tokens": {key: value["nativeUsageTotals"].get(key) for key in ("inputTokens", "outputTokens")},
                    "cost": None, "peak_memory_bytes": None, "energy_joules": None,
                    "failure_modes": failure, "ledger_source": ledger_path,
                    "ledger_sha256": ledger_sha, "ledger_chain_head": head,
                    "condition_sha256": value["conditionSha256"], "source_sha256": value["sourceSha256"],
                })
    return records, sources


def resolved_attribution(root, task, repeat, model, run):
    """Keep split panels immutable; accept only published, artifact-bound adjudication."""
    path = Path(root) / "attribution" / task / f"repeat-{repeat}" / model / "attribution.json"
    original = json.loads(path.read_bytes())
    if original["cause"] != "unresolved":
        return original, None
    matches = []
    for candidate in (ROOT / "benchmarks/michael/curriculum").glob("MBR3-*-resolution.json"):
        receipt = json.loads(candidate.read_bytes())
        if (receipt.get("task"), receipt.get("repeat"), receipt.get("model"),
                receipt.get("evidence_root")) == (task, repeat, model, Path(root).name):
            matches.append((candidate, receipt))
    if not matches:
        return original, None
    if len(matches) != 1:
        raise ValueError("ambiguous published attribution resolution")
    candidate, receipt = matches[0]
    bindings = {"originalPanelSha256": path, "outcomeSha256": run / "outcome.json",
                "collectedArtifactsSha256": run / "collected-source.bin",
                "graderReportSha256": run / "independent-grader/report.json"}
    if (receipt.get("kind") != "deterministic-attribution-resolution" or
            receipt.get("cause") != "model" or receipt.get("counts_as_model_failure") is not True or
            receipt.get("subject_rerun") is not False or any(
                receipt.get(key) != hashlib.sha256(file.read_bytes()).hexdigest()
                for key, file in bindings.items())):
        raise ValueError("published attribution resolution mismatch")
    resolved = {**original, "cause": "model", "deterministicEvidence": "\n".join(receipt["evidence"])}
    if failure_modes(resolved) != receipt["failure_modes"]:
        raise ValueError("published attribution resolution vocabulary mismatch")
    return resolved, hashlib.sha256(candidate.read_bytes()).hexdigest()


def ledger_records(root, *, selected=None):
    """Read completed round-three slots directly; never accept hand-authored outcome rows."""
    records = []
    observed = set()
    for path in sorted(Path(root).glob("trials/*/repeat-*/ledger.jsonl")):
        raw = path.read_bytes()
        states, _, head = Ledger(path)._read(io.BytesIO(raw))
        repeat = int(path.parent.name.removeprefix("repeat-"))
        for model, trial in sorted(states.items()):
            frozen = trial["bundle"]["agent"]["configuration"]["value"]
            name = frozen["package"]
            attempt_key = name, repeat, model
            if selected is not None and attempt_key not in selected:
                continue
            if len(trial["starts"]) != 1 or len(trial["attempts"]) != 1 or trial["origin"] != "new_trial":
                raise ValueError("incomplete or retried matrix ledger slot")
            attempt = trial["attempts"][0]
            if attempt["verdict"] not in ("passed", "failed"):
                raise ValueError("ungraded matrix attempt; attribution required")
            run = path.parent / model
            outcome = json.loads((run / "outcome.json").read_bytes())
            native = json.loads((run / "receipt/terminal.json").read_bytes())
            source_sha = hashlib.sha256((run / "collected-source.bin").read_bytes()).hexdigest()
            if (outcome["conditionSha256"] != condition_digest(frozen) or
                    outcome["sourceSha256"] != source_sha or native["wholeProcessQuiescent"] is not True or
                    native["cleanupSeconds"] > 15):
                raise ValueError("matrix native condition/artifact/cleanup mismatch")
            passed = attempt["verdict"] == "passed"
            timing = attempt["time_to_verified_completion"]
            seconds = timing["value"]["seconds"] if passed and timing["status"] == "known" else None
            if passed != (outcome["status"] == "pass") or seconds != outcome["completionSeconds"]:
                raise ValueError("matrix ledger/native result mismatch")
            failures = []
            resolution_sha = None
            if not passed:
                attribution, resolution_sha = resolved_attribution(root, name, repeat, model, run)
                if attribution["cause"] != "model":
                    raise ValueError("non-model matrix failure requires corrected primary attempt")
                failures = failure_modes(attribution)
            local = frozen.get("localInference")
            if local and ((native.get("localInference", {}).get("release") or {}).get(
                    "ownedRequestsDrained") is not True or native["nativePrompts"] != 0):
                raise ValueError("matrix local backend drain/prompt mismatch")
            usage = ([event.get("usage") for event in native["localInference"]["events"]
                      if event["type"] == "local_request_finished"] if local else native["usage"])
            tokens = {}
            for key in ("inputTokens", "outputTokens"):
                values = [value.get(key) if isinstance(value, dict) else None
                          for value in usage] if isinstance(usage, list) else []
                tokens[key] = sum(values) if values and all(type(v) is int for v in values) else None
            records.append({"task": name, "repeat": repeat, "model": model,
                "deployment_class": "local laptop" if local else "cloud",
                "condition": frozen["condition"], "tool_host": "local macOS MXC", "round": "v3",
                "family": curriculum.meta(name)["family"], "size": size(name), "resolved": passed,
                "completion_seconds": seconds, "tokens": tokens, "cost": None,
                "peak_memory_bytes": None, "energy_joules": None,
                "failure_modes": failures,
                "ledger_source": str(Path(Path(root).name) / path.relative_to(root)),
                "ledger_sha256": hashlib.sha256(raw).hexdigest(),
                "ledger_chain_head": head, "condition_sha256": outcome["conditionSha256"],
                "source_sha256": source_sha,
                **({"attribution_resolution_sha256": resolution_sha} if resolution_sha else {}),
                "transport_source_sha256": condition_digest(frozen["source"]),
                "transport_owner_sha256": frozen["source"]["benchmarks/michael/local_transport/owner.mjs"]})
            observed.add(attempt_key)
    if selected is not None and observed != selected:
        raise ValueError("incomplete selected round-three cohort")
    if not records:
        raise ValueError("no completed round-three ledger records")
    return records


def epoch_records(plan_path):
    """Resolve only the published recovery plan; outcomes still come from verified ledgers."""
    plan = json.loads(Path(plan_path).read_bytes())
    paths = [ROOT / "benchmarks/michael/local_transport" / name for name in (
        "mbr3-tooltip-verification.json", "mbr3-parity-verification.json",
        "mbr3-discovery-verification.json")]
    matches = [path for path in paths if path.is_file() and
               json.loads(path.read_bytes()).get("primaryPlan") == plan]
    if len(matches) != 1:
        raise ValueError("source epoch plan differs from published verification")
    verification_path = matches[0]
    if "paritySweepSha256" in plan:
        sweep = verification_path.with_name("mbr3-discovery-parity.json")
        if hashlib.sha256(sweep.read_bytes()).hexdigest() != plan["paritySweepSha256"]:
            raise ValueError("source epoch parity sweep mismatch")
    parent = Path(plan_path).parent.parent
    if hashlib.sha256((parent / "mbr3-v1/schedule.json").read_bytes()).hexdigest() != plan["scheduleSha256"]:
        raise ValueError("source epoch schedule mismatch")
    selections = {}
    labels = {}
    for row in plan["attempts"]:
        alias = row["evidence_root"]
        if alias not in ("mbr3-v1", "mbr3-tooltip-v2", "mbr3-parity-v3", "mbr3-discovery-v4"):
            raise ValueError("source epoch evidence alias denied")
        key = row["task"], row["repeat"], row["model"]
        if key in labels:
            raise ValueError("duplicate source epoch attempt")
        selections.setdefault(alias, set()).add(key)
        labels[key] = row["source_epoch"]
    priors = plan.get("excluded_priors") or [plan["excluded_prior"]]
    safe_priors = []
    for prior in priors:
        alias = prior.get("evidence_root", "mbr3-v1")
        if alias not in ("mbr3-v1", "mbr3-tooltip-v2", "mbr3-parity-v3"):
            raise ValueError("source epoch prior alias denied")
        prior_root = parent / alias
        outcome_path = prior_root / "trials" / prior["task"] / f"repeat-{prior['repeat']}" / prior["model"] / "outcome.json"
        attribution_path = prior_root / "attribution" / prior["task"] / f"repeat-{prior['repeat']}" / prior["model"] / "attribution.json"
        if (hashlib.sha256(outcome_path.read_bytes()).hexdigest() != prior["outcomeSha256"] or
                hashlib.sha256(attribution_path.read_bytes()).hexdigest() != prior["attributionSha256"] or
                json.loads(attribution_path.read_bytes())["cause"] != "harness"):
            raise ValueError("source epoch prior attribution mismatch")
        safe_priors.append({
            "task": prior["task"], "model": prior["model"], "round": "v3", "status": "ungraded",
            "failure_modes": prior.get("failure_modes", ["harness-error"]),
            "provenance": {"attribution_sha256": prior["attributionSha256"],
                           "outcome_sha256": prior["outcomeSha256"],
                           "cutoff": prior.get("cutoff", "harness"),
                           "excluded_from_task_failures": True},
        })
    records = []
    for alias, selected in selections.items():
        safety_path = parent / alias / "safety.json"
        safety_bytes = safety_path.read_bytes()
        safety = json.loads(safety_bytes)
        for row in ledger_records(parent / alias, selected=selected):
            epoch = labels[row["task"], row["repeat"], row["model"]]
            if row["transport_owner_sha256"] != plan["source_epochs"][epoch]["ownerSha256"]:
                raise ValueError("source epoch native owner mismatch")
            if (hashlib.sha256(safety_bytes).hexdigest() != plan["source_epochs"][epoch]["safetySha256"] or
                    safety.get("passed") is not True or
                    row["transport_source_sha256"] != condition_digest(safety["source"])):
                raise ValueError("source epoch full native source/safety mismatch")
            row["condition"] += "/" + epoch
            records.append(row)
    source = {"path": str(verification_path.relative_to(ROOT)),
              "sha256": hashlib.sha256(verification_path.read_bytes()).hexdigest(),
              "role": "Published native source epochs and complete logical-attempt selection",
              "prior_attempts": safe_priors}
    return records, source


def sealed_epoch_records(path):
    """Reproduce published cohorts without depending on the executor's owned state."""
    data = json.loads(path.read_bytes())
    filename = data["archiveFile"]
    if Path(filename).name != filename or not filename.endswith(".tar.gz"):
        raise ValueError("matrix archive filename denied")
    archive_path = path.with_name(filename)
    with archive_path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != data["archiveSha256"]:
            raise ValueError("matrix epoch archive mismatch")
    found, total = set(), 0
    with tempfile.TemporaryDirectory(prefix="michael-matrix-") as directory:
        root = Path(directory)
        with tarfile.open(archive_path, "r|gz") as archive:
            for member in archive:
                relative = PurePosixPath(member.name)
                total += member.size
                if (not relative.parts or relative.is_absolute() or ".." in relative.parts or "\\" in member.name or
                        str(relative) != member.name or not member.isfile() or member.name in found or
                        member.name not in data["members"] or not 0 <= member.size <= 16777216 or total > 1073741824):
                    raise ValueError("matrix epoch archive member denied")
                raw = archive.extractfile(member).read()
                if hashlib.sha256(raw).hexdigest() != data["members"][member.name]:
                    raise ValueError("matrix epoch archived member mismatch")
                target = root.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                found.add(member.name)
        if found != set(data["members"]) or data["primaryPlanPath"] not in found:
            raise ValueError("matrix epoch archive incomplete")
        records, epoch_source = epoch_records(root / data["primaryPlanPath"])
        for alias in data.get("localRunRoots", []):
            if Path(alias).name != alias or not alias.startswith("mbr3-local-"):
                raise ValueError("matrix local archive alias denied")
            local = ledger_records(root / alias)
            if any(row["deployment_class"] != "local laptop" for row in local):
                raise ValueError("matrix local archive condition mismatch")
            records.extend(local)
    sources = [epoch_source, {"path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "role": "Sealed round-three ledger/artifact/native-metadata archive index"},
        {"path": str(archive_path.relative_to(ROOT)), "sha256": data["archiveSha256"],
         "role": "Validated ledger chains and exact artifacts; native terminal is an explicit safe projection"}]
    return records, sources


def default_records():
    records, sources = seed()
    for name in ("MBR3-verification.json", "MBR3-cloud-verification.json", "MBR3-core-verification.json"):
        path = ROOT / "benchmarks/michael/curriculum" / name
        if path.is_file():
            additional, evidence = sealed_epoch_records(path)
            records.extend(additional)
            sources.extend(evidence)
            break
    return records, sources


def build(records, *, threshold=0.8, minimum_n=5, objective="fastest"):
    if not 0 < threshold < 1 or minimum_n < 1 or objective not in ("fastest", "cheapest"):
        raise ValueError("invalid declared routing policy")
    groups = {}
    targets = {}
    columns = set()
    seen = set()
    seen_ledgers = set()
    for row in records:
        key = row["condition"], row["model"], row["task"], row["repeat"]
        if key in seen or type(row["resolved"]) is not bool or row["deployment_class"] not in CLASSES:
            raise ValueError("duplicate/invalid observed record")
        if any(v is not None and (type(v) not in (int, float) or not isfinite(v) or v < 0)
               for v in (row["cost"], row["peak_memory_bytes"], row["energy_joules"])):
            raise ValueError("invalid observed measurement")
        if any(v is not None and (type(v) is not int or v < 0) for v in row["tokens"].values()):
            raise ValueError("invalid observed tokens")
        if any(mode not in FAILURE_MODES for mode in row["failure_modes"]):
            raise ValueError("invalid controlled failure mode")
        seen.add(key)
        if row.get("ledger_sha256"):
            identity = row["ledger_sha256"], row["model"], row["task"], row["repeat"]
            if identity in seen_ledgers:
                raise ValueError("duplicate matrix ledger slot across conditions")
            seen_ledgers.add(identity)
        target = row["condition"] + ":" + row["model"]
        info = {"model": row["model"], "deployment_class": row["deployment_class"],
                "condition": row["condition"], "tool_host": row["tool_host"]}
        if target in targets and targets[target] != info:
            raise ValueError("target deployment changed within condition")
        targets[target] = info
        column = row["family"] + " × " + row["size"]["tier"]
        if row["size"]["tier"] not in ("small", "medium", "large"):
            raise ValueError("invalid agent-native size tier")
        columns.add(column)
        groups.setdefault((target, column), []).append(row)
    cells = {}
    for (target, column), rows in sorted(groups.items()):
        successes = sum(r["resolved"] for r in rows)
        times = [r["completion_seconds"] for r in rows if r["resolved"]]
        if any(type(t) not in (int, float) or not isfinite(t) or t < 0 for t in times):
            raise ValueError("success without verified completion")
        def measured(key):
            values = [r[key] for r in rows]
            return {"status": "unknown", "value": None} if any(v is None for v in values) else {
                "status": "known", "value": max(values) if key == "peak_memory_bytes" else sum(values)}
        tokens = {}
        for key in ("inputTokens", "outputTokens"):
            values = [r["tokens"][key] for r in rows]
            tokens[key] = None if any(v is None for v in values) else sum(values)
        cells.setdefault(target, {})[column] = {
            "n": len(rows), "tasks": len({r["task"] for r in rows}), "successes": successes,
            "success_rate": successes / len(rows), "wilson_ci95": list(wilson(successes, len(rows))),
            "verified_time_n": len(times), "median_verified_seconds": median(times) if times else None,
            "tokens": tokens, "cost": measured("cost"), "peak_memory_bytes": measured("peak_memory_bytes"),
            "energy_joules": measured("energy_joules"),
            "failure_modes": dict(sorted(Counter(mode for r in rows for mode in set(r["failure_modes"])).items())),
            "provenance": [{"task": r["task"], "repeat": r["repeat"], "round": r["round"],
                "condition_sha256": r["condition_sha256"], "source_sha256": r["source_sha256"],
                "ledger_source": r["ledger_source"], "ledger_sha256": r.get("ledger_sha256"),
                "ledger_chain_head": r.get("ledger_chain_head"), "size": r["size"],
                **({"attribution_resolution_sha256": r["attribution_resolution_sha256"]}
                   if "attribution_resolution_sha256" in r else {})} for r in rows],
        }
    recommendations = {}
    for column in sorted(columns):
        eligible = []
        for target, target_cells in cells.items():
            cell = target_cells.get(column)
            if not cell or cell["n"] < minimum_n or cell["wilson_ci95"][0] < threshold:
                continue
            score = cell["median_verified_seconds"] if objective == "fastest" else (
                cell["cost"]["value"] / cell["n"] if cell["cost"]["status"] == "known" else None)
            if score is not None:
                eligible.append((score, target))
        recommendations[column] = {"status": "recommended" if eligible else "insufficient evidence",
            "target": min(eligible)[1] if eligible else None}
    return {"schema_version": 1, "targets": targets, "columns": sorted(columns), "cells": cells,
        "routing_policy": {"objective": objective, "minimum_n": minimum_n, "lower_ci_threshold": threshold},
        "recommendations": recommendations,
        "size_policy": {"small": "oracle diff <=1 file and <=100 changed lines",
            "medium": "oracle diff <=4 files and <=400 changed lines", "large": "otherwise",
            "limits": "Declared heuristic, not measured human effort; base/oracle only, not subject outcome."},
        "limits": "Condition-separated retrospective cells; repeated tasks are correlated. "
            "Cloud denotes inference deployment, not tool execution location. Unknown cost/energy/memory are not zero."}


def validate(value):
    required = json.loads((HERE / "schema.json").read_text())["required"]
    if set(value) != set(required) or value["schema_version"] != 1:
        raise ValueError("matrix schema fields")
    if set(value["targets"]) != set(value["cells"]) or sorted(value["recommendations"]) != value["columns"]:
        raise ValueError("matrix schema target/column alignment")
    for target in value["targets"].values():
        if target["deployment_class"] not in CLASSES:
            raise ValueError("matrix schema deployment")
    for target_cells in value["cells"].values():
        for column, cell in target_cells.items():
            if column not in value["columns"] or type(cell["n"]) is not int or cell["n"] < 1:
                raise ValueError("matrix schema sample count")
            if not 0 <= cell["successes"] <= cell["n"] or not 0 <= cell["wilson_ci95"][0] <= cell["wilson_ci95"][1] <= 1:
                raise ValueError("matrix schema rates")
            if cell["success_rate"] != cell["successes"] / cell["n"] or len(cell["provenance"]) != cell["n"]:
                raise ValueError("matrix schema observed counts")
            for key in ("cost", "peak_memory_bytes", "energy_joules"):
                measured = cell[key]
                if measured["status"] not in ("known", "unknown") or (
                    measured["status"] == "unknown" and measured["value"] is not None) or (
                    measured["status"] == "known" and (type(measured["value"]) not in (int, float) or
                        not isfinite(measured["value"]) or measured["value"] < 0)):
                    raise ValueError("matrix schema unknown measurement")
            if cell["verified_time_n"] != cell["successes"] or (
                cell["successes"] == 0 and cell["median_verified_seconds"] is not None):
                raise ValueError("matrix schema verification time")
            if any(mode not in FAILURE_MODES or type(n) is not int or not 1 <= n <= cell["n"]
                   for mode, n in cell["failure_modes"].items()):
                raise ValueError("matrix schema failure modes")


def markdown(value):
    lines = ["# Delegation matrix", "", "Generated from verified ledger-derived records; do not hand-edit.",
        "Rows are inference targets and frozen conditions. Tools remain on the indicated host.",
        "Unobserved deployment classes have no invented cells. Repeated exposure and sparse samples limit routing.", "",
        "| Target / condition | Deployment | Family × size | n | Success (95% Wilson) | Median verified s | Input / output tokens | Cost; peak memory; energy | Failure modes |",
        "|---|---|---|---:|---|---:|---:|---|---|"]
    for target, cells in value["cells"].items():
        for column, cell in cells.items():
            info = value["targets"][target]
            lo, hi = cell["wilson_ci95"]
            tokens = " / ".join("unknown" if v is None else f"{v:,}" for v in cell["tokens"].values())
            measured = "; ".join(str(cell[k]["value"]) if cell[k]["status"] == "known" else "unknown"
                for k in ("cost", "peak_memory_bytes", "energy_joules"))
            time = "unknown" if cell["median_verified_seconds"] is None else f"{cell['median_verified_seconds']:.2f}"
            failures = "; ".join(f"{mode} ×{n}" for mode, n in cell["failure_modes"].items()) or "none observed"
            lines.append(f"| {target} | {info['deployment_class']} | {column} | {cell['n']} | "
                f"{cell['successes']}/{cell['n']} ({lo:.1%}–{hi:.1%}) | {time} | {tokens} | {measured} | {failures} |")
    policy = value["routing_policy"]
    lines += ["", "## Derived routing", "",
        f"Objective: {policy['objective']}; minimum n={policy['minimum_n']}; "
        f"95% lower bound ≥{policy['lower_ci_threshold']:.0%}. No fallback model is invented.",
        "", "| Family × size | Recommendation |", "|---|---|"]
    for column, recommendation in value["recommendations"].items():
        lines.append(f"| {column} | {recommendation['target'] or recommendation['status']} |")
    lines += ["", "## Provenance and prior attempts", "",
        "Selection/provenance is not a failure mode. Per-cell JSON provenance binds the exact ledger, "
        "chain head, frozen condition and artifact hashes. Native measurements come from the sealed index.",
        "The following deterministically attributed prior attempts are excluded from primary cell denominators.",
        "", "| Task | Target | Round | Status | Failure modes |", "|---|---|---|---|---|"]
    for source in value.get("sources", []):
        for row in source.get("prior_attempts", []):
            modes = "; ".join(f"{mode} ×1" for mode in row["failure_modes"])
            lines.append(f"| {row['task']} | {row['model']} | {row['round']} | {row['status']} | {modes} |")
    lines += ["", "## Size and limits", "", json.dumps(value["size_policy"], sort_keys=True), "", value["limits"], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, action="append", default=[],
                        help="Round-three evidence root containing trials/*/repeat-*/ledger.jsonl")
    parser.add_argument("--source-epoch-plan", type=Path,
                        help="Published tooltip-recovery primary-plan.json; requires complete selected slots")
    args = parser.parse_args()
    records, sources = seed() if args.run_root or args.source_epoch_plan else default_records()
    for root in args.run_root:
        records.extend(ledger_records(root))
    if args.source_epoch_plan:
        selected, source = epoch_records(args.source_epoch_plan)
        records.extend(selected)
        sources.append(source)
    value = build(records)
    value["sources"] = sources
    validate(value)
    (HERE / "matrix.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    (HERE / "matrix.md").write_text(markdown(value))


if __name__ == "__main__":
    main()
