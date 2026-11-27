"""Generate condition-separated targets from verified ledger-derived records."""
import argparse
import difflib
import hashlib
import io
import json
import tarfile
from pathlib import Path
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


def archived_ledgers(data, path, selected):
    with path.open("rb") as stream:
        archive_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    if archive_sha != data["archiveSha256"]:
        raise ValueError("matrix evidence archive mismatch")
    found = {}
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
        ledgers, archive_sha = archived_ledgers(data, archive_path, set(selections.values()))
        sources.append({"path": str(archive_path.relative_to(ROOT)), "sha256": archive_sha,
                        "role": "sealed ledger bytes; hash chain and frozen bundles validated"})
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
                    failure = [row["reason"] for row in data.get("attemptClassifications", [])
                        if row["task"] == task and row["model"] == model and row["primary"]]
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


def ledger_records(root):
    """Read completed round-three slots directly; never accept hand-authored outcome rows."""
    records = []
    for path in sorted(Path(root).glob("trials/*/repeat-*/ledger.jsonl")):
        raw = path.read_bytes()
        states, _, head = Ledger(path)._read(io.BytesIO(raw))
        repeat = int(path.parent.name.removeprefix("repeat-"))
        for model, trial in sorted(states.items()):
            if len(trial["starts"]) != 1 or len(trial["attempts"]) != 1 or trial["origin"] != "new_trial":
                raise ValueError("incomplete or retried matrix ledger slot")
            attempt = trial["attempts"][0]
            if attempt["verdict"] not in ("passed", "failed"):
                raise ValueError("ungraded matrix attempt; attribution required")
            frozen = trial["bundle"]["agent"]["configuration"]["value"]
            name = frozen["package"]
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
            if not passed:
                attribution_path = Path(root) / "attribution" / name / path.parent.name / model / "attribution.json"
                attribution = json.loads(attribution_path.read_bytes())
                if attribution["cause"] != "model":
                    raise ValueError("non-model matrix failure requires corrected primary attempt")
                failures = sorted({json.dumps(item, sort_keys=True) if not isinstance(item, str) else item
                    for verdict in attribution["verdicts"] for item in verdict["evidence"]})
            usage = native["usage"]
            tokens = {}
            for key in ("inputTokens", "outputTokens"):
                values = [value.get(key) for value in usage] if isinstance(usage, list) else []
                tokens[key] = sum(values) if values and all(type(v) is int for v in values) else None
            records.append({"task": name, "repeat": repeat, "model": model, "deployment_class": "cloud",
                "condition": frozen["condition"], "tool_host": "local macOS MXC", "round": "v3",
                "family": curriculum.meta(name)["family"], "size": size(name), "resolved": passed,
                "completion_seconds": seconds, "tokens": tokens, "cost": None,
                "peak_memory_bytes": None, "energy_joules": None,
                "failure_modes": failures,
                "ledger_source": str(path), "ledger_sha256": hashlib.sha256(raw).hexdigest(),
                "ledger_chain_head": head, "condition_sha256": outcome["conditionSha256"],
                "source_sha256": source_sha})
    if not records:
        raise ValueError("no completed round-three ledger records")
    return records


def build(records, *, threshold=0.8, minimum_n=5, objective="fastest"):
    if not 0 < threshold < 1 or minimum_n < 1 or objective not in ("fastest", "cheapest"):
        raise ValueError("invalid declared routing policy")
    groups = {}
    targets = {}
    columns = set()
    seen = set()
    for row in records:
        key = row["condition"], row["model"], row["task"], row["repeat"]
        if key in seen or type(row["resolved"]) is not bool or row["deployment_class"] not in CLASSES:
            raise ValueError("duplicate/invalid observed record")
        if any(v is not None and (type(v) not in (int, float) or not isfinite(v) or v < 0)
               for v in (row["cost"], row["peak_memory_bytes"], row["energy_joules"])):
            raise ValueError("invalid observed measurement")
        if any(v is not None and (type(v) is not int or v < 0) for v in row["tokens"].values()):
            raise ValueError("invalid observed tokens")
        seen.add(key)
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
            "failure_modes": sorted({mode for r in rows for mode in r["failure_modes"]}),
            "provenance": [{"task": r["task"], "repeat": r["repeat"], "round": r["round"],
                "condition_sha256": r["condition_sha256"], "source_sha256": r["source_sha256"],
                "ledger_source": r["ledger_source"], "ledger_sha256": r.get("ledger_sha256"),
                "ledger_chain_head": r.get("ledger_chain_head"), "size": r["size"]} for r in rows],
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
            failures = ("; ".join(cell["failure_modes"]) or "none observed").replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {target} | {info['deployment_class']} | {column} | {cell['n']} | "
                f"{cell['successes']}/{cell['n']} ({lo:.1%}–{hi:.1%}) | {time} | {tokens} | {measured} | {failures} |")
    policy = value["routing_policy"]
    lines += ["", "## Derived routing", "",
        f"Objective: {policy['objective']}; minimum n={policy['minimum_n']}; "
        f"95% lower bound ≥{policy['lower_ci_threshold']:.0%}. No fallback model is invented.",
        "", "| Family × size | Recommendation |", "|---|---|"]
    for column, recommendation in value["recommendations"].items():
        lines.append(f"| {column} | {recommendation['target'] or recommendation['status']} |")
    lines += ["", "## Size and limits", "", json.dumps(value["size_policy"], sort_keys=True), "", value["limits"], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, action="append", default=[],
                        help="Round-three evidence root containing trials/*/repeat-*/ledger.jsonl")
    args = parser.parse_args()
    records, sources = seed()
    for root in args.run_root:
        records.extend(ledger_records(root))
    value = build(records)
    value["sources"] = sources
    validate(value)
    (HERE / "matrix.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    (HERE / "matrix.md").write_text(markdown(value))


if __name__ == "__main__":
    main()
