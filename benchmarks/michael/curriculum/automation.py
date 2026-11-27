"""Automated task admission, failure attribution and quality signals (no human review).

Deterministic steps run here. Model steps (task audit, blind re-implementation,
failure attribution, quality panel) are frozen, hash-bound requests with
strict JSON verdict schemas. The local executor runs them; this module
validates their verdicts and applies fixed decision rules. Model verdicts gate
task admission and label failures. They never set a pass/fail score: that
comes only from the independent grader.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import io
import json
import re
import tokenize

PROMPT_VERSION = "mb008-v1"

AUDIT_PROMPT = """You audit a benchmark task before admission. You see the public
instruction, the hidden verifier (tests/clauses) and the oracle solution.
Report, as strict JSON matching the schema, every:
- leakage: the instruction or visible files reveal the oracle or hidden checks;
- untested_requirement: an instruction requirement that no check verifies;
- overspecified_test: a check that rejects behavior the instruction allows;
- contradiction: instruction, checks and oracle disagree.
Cite the exact check id or instruction sentence for each finding. Do not score
any model. Output only JSON."""

BLIND_PROMPT = """Solve the task using only the instruction and the provided files.
You will not see tests. Produce the requested artifact."""

ADJUDICATE_PROMPT = """A blind solver's artifact failed the hidden checks listed below.
Using only the instruction, decide whether the artifact is a reasonable
solution that the checks wrongly reject (task-caused) or a genuine failure to
meet the instruction (solver-caused). Cite the instruction sentence. JSON only."""

ATTRIBUTION_PROMPT = """Read the agent trajectory, final patch and verifier log for a
failed benchmark attempt. Label the failure cause as exactly one of
model (the agent did not meet the instruction), task (instruction/checks are
wrong, ambiguous or leak), or harness (tooling, limits, transport, environment).
Cite concrete evidence lines. JSON only."""

PANEL_RUBRIC = """Compare two solutions, A and B, to the same instruction. Both
passed the functional checks. Judge only code quality: correctness risk,
clarity, minimality/locality of change, consistency with surrounding code,
absence of debug or dead code, and maintainability. Answer strict JSON:
{"preferred": "A"|"B"|"tie", "scores": {"A": 1-5, "B": 1-5}, "reasons": [..]}."""

SCHEMAS = {
    "audit": {"findings": list, "admit": bool},
    "adjudication": {"cause": ("task", "solver"), "citation": str},
    "attribution": {"cause": ("model", "task", "harness"), "confidence": float, "evidence": list},
    "panel": {"preferred": ("A", "B", "tie"), "scores": dict, "reasons": list},
}
FINDING_KINDS = ("leakage", "untested_requirement", "overspecified_test", "contradiction")


def _sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def request(kind: str, *, model: str, family: str, payload: dict, excluded_families: tuple = ()) -> dict:
    """Frozen, hash-bound model request; the executor must echo request_sha256."""
    if family in excluded_families:
        raise ValueError(f"{kind}: model family {family!r} is excluded for this request")
    prompt = {"audit": AUDIT_PROMPT, "blind": BLIND_PROMPT, "adjudication": ADJUDICATE_PROMPT,
              "attribution": ATTRIBUTION_PROMPT, "panel": PANEL_RUBRIC}[kind]
    body = {"kind": kind, "prompt_version": PROMPT_VERSION, "prompt": prompt, "model": model,
            "family": family, "payload": payload}
    return {**body, "request_sha256": _sha(body), "status": "pending_executor"}


def validate_verdict(kind: str, verdict: dict, req: dict) -> dict:
    if verdict.get("request_sha256") != req["request_sha256"]:
        raise ValueError("verdict is not bound to this request")
    body = verdict.get("verdict")
    schema = SCHEMAS[kind]
    if not isinstance(body, dict) or set(body) != set(schema):
        raise ValueError(f"{kind}: verdict fields must be exactly {sorted(schema)}")
    for key, rule in schema.items():
        value = body[key]
        if isinstance(rule, tuple):
            if value not in rule:
                raise ValueError(f"{kind}.{key}: expected one of {rule}")
        elif rule is float:
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ValueError(f"{kind}.{key}: expected probability")
        elif not isinstance(value, rule):
            raise ValueError(f"{kind}.{key}: expected {rule.__name__}")
    if kind == "audit":
        for finding in body["findings"]:
            if not isinstance(finding, dict) or finding.get("kind") not in FINDING_KINDS or not finding.get("citation"):
                raise ValueError("audit finding needs a known kind and a citation")
    if kind == "panel":
        if set(body["scores"]) != {"A", "B"} or any(type(v) is not int or not 1 <= v <= 5 for v in body["scores"].values()):
            raise ValueError("panel scores must be integers 1-5 for A and B")
    return body


# --- Admission ---------------------------------------------------------------------------

def admission(*, oracle_passes: bool, base_fails: bool, audits: list[dict] | None,
              blind: list[dict] | None) -> dict:
    """Fixed gate rules. ``audits``: validated audit verdicts (>=2 families).
    ``blind``: [{"passed": bool, "adjudication": validated verdict | None}]."""
    reasons = []
    if not oracle_passes:
        reasons.append("oracle_fails")
    if not base_fails:
        reasons.append("base_passes")
    if reasons:
        return {"state": "needs_fix", "reasons": reasons}
    if audits is None or blind is None:
        return {"state": "provisional", "reasons": ["model gates pending executor"]}
    if len(audits) < 2:
        return {"state": "provisional", "reasons": ["need audits from two model families"]}
    findings = [f for audit in audits for f in audit["findings"]]
    if any(f["kind"] in ("leakage", "contradiction") for f in findings):
        return {"state": "needs_fix", "reasons": sorted({f["kind"] for f in findings})}
    rejected = [b for b in blind if not b["passed"] and (b.get("adjudication") or {}).get("cause") == "task"]
    if rejected:
        return {"state": "needs_fix", "reasons": ["tests reject a reasonable blind solution"]}
    if any(not b["passed"] and b.get("adjudication") is None for b in blind):
        return {"state": "provisional", "reasons": ["blind failure awaiting adjudication"]}
    if any(f["kind"] in ("untested_requirement", "overspecified_test") for f in findings):
        return {"state": "admitted_with_findings", "reasons": sorted({f["kind"] for f in findings})}
    return {"state": "admitted", "reasons": []}


# --- Failure attribution ----------------------------------------------------------------

def route_failure(verdicts: list[dict], *, threshold: float = 0.7) -> dict:
    """Two attributor families must agree with confidence; otherwise rerun as suspect."""
    causes = {v["cause"] for v in verdicts}
    confident = all(v["confidence"] >= threshold for v in verdicts)
    if len(verdicts) >= 2 and len(causes) == 1 and confident:
        cause = causes.pop()
        action = {"model": "record_model_result", "task": "fix_task_and_rerun",
                  "harness": "fix_harness_and_rerun"}[cause]
        return {"cause": cause, "action": action, "counts_as_model_failure": cause == "model"}
    return {"cause": "unresolved", "action": "rerun_once_then_reattribute", "counts_as_model_failure": False}


# --- Deterministic quality signals (reported separately from pass/fail) ---------------

DEBUG = re.compile(rb"(^|\s)(print\(|console\.log\(|debugger;|breakpoint\(\)|import pdb|pdb\.set_trace)")
MARKERS = re.compile(rb"\b(TODO|FIXME|XXX|HACK)\b")


def _changed_lines(before: bytes, after: bytes) -> tuple[int, int, list[bytes]]:
    added, removed, new = 0, 0, []
    for line in difflib.diff_bytes(difflib.unified_diff, before.splitlines(), after.splitlines(), lineterm=b"", n=0):
        if line.startswith(b"+") and not line.startswith(b"+++"):
            added += 1
            new.append(line[1:])
        elif line.startswith(b"-") and not line.startswith(b"---"):
            removed += 1
    return added, removed, new


def _unreachable(source: bytes) -> int:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return -1
    count = 0
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list):
                for index, statement in enumerate(block[:-1]):
                    if isinstance(statement, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                        count += len(block) - index - 1
                        break
    return count


def deterministic_quality(*, base: dict[str, bytes], candidate: dict[str, bytes],
                          oracle: dict[str, bytes], writable: list[str]) -> dict:
    """Parse-only static signals; candidate code is never executed or imported."""
    paths = sorted(set(base) | set(candidate))
    touched = [p for p in paths if base.get(p) != candidate.get(p)]
    added = removed = 0
    new_lines: list[bytes] = []
    for path in touched:
        a, r, lines = _changed_lines(base.get(path, b""), candidate.get(path, b""))
        added, removed, new_lines = added + a, removed + r, new_lines + lines
    oracle_size, oracle_lines = 0, []
    for path in sorted(set(oracle) | set(base)):
        if path in oracle and base.get(path) != oracle.get(path):
            a, r, lines = _changed_lines(base.get(path, b""), oracle[path])
            oracle_size, oracle_lines = oracle_size + a + r, oracle_lines + lines
    debug = sum(bool(DEBUG.search(line)) for line in new_lines)
    markers = sum(bool(MARKERS.search(line)) for line in new_lines)
    python = [p for p in touched if p.endswith(".py") and p in candidate]
    return {
        "files_touched": len(touched),
        "files_outside_task": sorted(p for p in touched if p not in writable),
        "lines_added": added, "lines_removed": removed,
        "diff_size_vs_oracle": round((added + removed) / oracle_size, 3) if oracle_size else None,
        "debug_statements_added": debug,
        "debug_beyond_oracle": max(0, debug - sum(bool(DEBUG.search(line)) for line in oracle_lines)),
        "todo_markers_added": markers,
        "todo_beyond_oracle": max(0, markers - sum(bool(MARKERS.search(line)) for line in oracle_lines)),
        "python_parse_errors": sum(_unreachable(candidate[p]) < 0 for p in python),
        "unreachable_statements": sum(max(0, _unreachable(candidate[p])) for p in python),
        "tests_added": sum(1 for line in new_lines if re.match(rb"\s*(def test_|it\(|test\()", line)),
    }


# --- Blind pairwise quality panel ----------------------------------------------------------

def panel_requests(*, task: str, instruction: str, candidate_diff: str, oracle_diff: str,
                   judges: list[tuple[str, str]], model_under_test_family: str) -> list[dict]:
    """Blind A/B order derived from a hash; >=2 judge families, none the model under test."""
    families = {family for _, family in judges}
    if len(families) < 2:
        raise ValueError("quality panel needs at least two model families")
    candidate_is_a = int(hashlib.sha256(f"{task}:{candidate_diff}".encode()).hexdigest(), 16) % 2 == 0
    a, b = (candidate_diff, oracle_diff) if candidate_is_a else (oracle_diff, candidate_diff)
    return [{**request("panel", model=model, family=family, excluded_families=(model_under_test_family,),
                       payload={"instruction": instruction, "A": a, "B": b}),
             "candidate_label": "A" if candidate_is_a else "B"} for model, family in judges]


def panel_score(requests: list[dict], verdicts: list[dict]) -> dict:
    """Secondary signal: candidate-vs-oracle preference and inter-judge agreement."""
    outcomes = []
    for req, verdict in zip(requests, verdicts):
        body = validate_verdict("panel", verdict, req)
        label = req["candidate_label"]
        outcomes.append("tie" if body["preferred"] == "tie" else
                        "candidate" if body["preferred"] == label else "oracle")
    pairs = [(x, y) for i, x in enumerate(outcomes) for y in outcomes[i + 1:]]
    return {"judgements": outcomes,
            "candidate_preferred_rate": outcomes.count("candidate") / len(outcomes),
            "pairwise_agreement": sum(x == y for x, y in pairs) / len(pairs) if pairs else None,
            "role": "secondary quality signal; never pass/fail"}


def degrade(source: bytes) -> dict[str, bytes]:
    """Seeded degraded variants of a known-good fix, for panel calibration."""
    lines = source.splitlines(keepends=True)
    first_def = next((i for i, line in enumerate(lines) if line.lstrip().startswith((b"def ", b"function "))), 0)
    indent = re.match(rb"\s*", lines[first_def + 1] if first_def + 1 < len(lines) else b"    ").group(0) or b"    "
    debug = lines[:first_def + 1] + [indent + b"print('DEBUG entering')  # TODO remove\n"] + lines[first_def + 1:]
    dead = lines + [b"\n\ndef _unused_helper(value):\n    return value\n    value = None\n"]
    names = re.findall(rb"\bdef ([a-z_][a-z0-9_]{3,})\(", source)
    private = [n for n in names if n.startswith(b"_")]
    renamed = source
    for index, name in enumerate(private[:3]):
        renamed = re.sub(rb"\b" + re.escape(name) + rb"\b", b"_f%d" % index, renamed)
    if renamed == source:
        tree = ast.parse(source)
        excluded = {n.arg for n in ast.walk(tree) if isinstance(n, (ast.arg, ast.keyword)) and n.arg}
        excluded.update(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute))
        excluded.update(n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef)))
        assigned = {target.id for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
                    for node in ast.walk(function) if isinstance(node, ast.Assign)
                    for target in node.targets if isinstance(target, ast.Name)}
        names = sorted(n for n in assigned if n.islower() and len(n) >= 4 and n not in excluded)[:3]
        mapping = {name: f"_q{index}" for index, name in enumerate(names)}
        renamed = tokenize.untokenize([
            token._replace(string=mapping.get(token.string, token.string)) if token.type == tokenize.NAME else token
            for token in tokenize.tokenize(io.BytesIO(source).readline)])
    if renamed == source:
        raise ValueError("source has no identifiers suitable for a distinct obscured-name fixture")
    return {"debug_leftover": b"".join(debug), "dead_code": b"".join(dead), "obscured_names": renamed}


def calibration_agreement(results: list[dict]) -> dict:
    """results: [{"variant", "judge", "preferred_oracle": bool}] on oracle-vs-degraded pairs."""
    judges = sorted({r["judge"] for r in results})
    accuracy = {j: sum(r["preferred_oracle"] for r in results if r["judge"] == j)
                / max(1, sum(r["judge"] == j for r in results)) for j in judges}
    by_variant: dict[str, list[bool]] = {}
    for r in results:
        by_variant.setdefault(r["variant"], []).append(r["preferred_oracle"])
    agree = [len(set(v)) == 1 for v in by_variant.values() if len(v) > 1]
    return {"judge_accuracy": accuracy, "pairwise_agreement": sum(agree) / len(agree) if agree else None,
            "admit_panel": bool(accuracy) and min(accuracy.values()) >= 0.8}
