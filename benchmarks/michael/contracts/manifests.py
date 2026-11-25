"""Pure JSON interchange v1. Valid declarations are not runtime attestations."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from typing import Any


class ManifestError(ValueError):
    """Invalid or unsupported contract data, with an actionable field path."""


def _object(value: Any, path: str, fields: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{path}: expected an object")
    if fields is not None and value.keys() - fields:
        raise ManifestError(f"{path}: unsupported fields {sorted(value.keys() - fields)}")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{path}: expected a nonempty string")
    return value


def _choice(value: Any, choices: set[str], path: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ManifestError(f"{path}: expected one of {sorted(choices)}")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ManifestError(f"{path}: expected an array")
    return value


def _number(value: Any, path: str, *, integer: bool = False) -> None:
    if type(value) not in (int, float) or (integer and type(value) is not int):
        raise ManifestError(f"{path}: expected a nonnegative {'integer' if integer else 'number'}")
    if value < 0 or (isinstance(value, float) and not math.isfinite(value)):
        raise ManifestError(f"{path}: expected a finite nonnegative duration/count")


def _json(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _text(key, path)
            _json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _json(child, f"{path}[{index}]")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ManifestError(f"{path}: JSON numbers must be finite")
    elif value is not None and not isinstance(value, (str, int, bool)):
        raise ManifestError(f"{path}: expected a JSON value")


def _digest(value: Any, path: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ManifestError(f"{path}: expected a lowercase 64-character SHA-256")


def _provenance(value: Any, path: str) -> None:
    _text(_object(value, path).get("source_id"), f"{path}.source_id")


def _reference(value: Any, path: str) -> None:
    ref = _object(value, path, {"id", "revision", "sha256"})
    for name in ("id", "revision"):
        _text(ref.get(name), f"{path}.{name}")
    _digest(ref.get("sha256"), f"{path}.sha256")


def _evidence(value: Any, path: str) -> dict[str, Any]:
    item = _object(value, path, {"status", "value", "reason", "source"})
    status = _choice(item.get("status"), {"known", "unknown", "unsupported", "not_applicable"}, f"{path}.status")
    _text(item.get("source"), f"{path}.source")
    if status == "known":
        if item.get("value") is None:
            raise ManifestError(f"{path}.value: known evidence requires a non-null value")
    else:
        _text(item.get("reason"), f"{path}.reason")
        if "value" in item:
            raise ManifestError(f"{path}.value: unavailable evidence must not invent a value")
    return item


def _timing(value: Any, path: str, scope: str) -> None:
    item = _evidence(value, path)
    if item["status"] != "known":
        return
    measurement = _object(item["value"], f"{path}.value", {
        "seconds", "scope", "clock", "host_ids", "coverage", "correlation_id",
    })
    _number(measurement.get("seconds"), f"{path}.seconds")
    if measurement.get("scope") != scope:
        raise ManifestError(f"{path}.scope: expected {scope!r}")
    clock = _choice(measurement.get("clock"), {"monotonic", "correlated_wall"}, f"{path}.clock")
    _choice(measurement.get("coverage"), {"complete", "partial"}, f"{path}.coverage")
    hosts = _array(measurement.get("host_ids"), f"{path}.host_ids")
    if not hosts:
        raise ManifestError(f"{path}.host_ids: measurement requires a host")
    for host in hosts:
        _text(host, f"{path}.host_ids")
    if len(set(hosts)) != len(hosts):
        raise ManifestError(f"{path}.host_ids: duplicate host")
    if clock == "monotonic" and len(hosts) != 1:
        raise ManifestError(f"{path}.clock: cannot subtract cross-host monotonic clocks")
    if clock == "correlated_wall":
        _text(measurement.get("correlation_id"), f"{path}.correlation_id")
    elif "correlation_id" in measurement:
        raise ManifestError(f"{path}.correlation_id: only correlated wall clocks use correlation evidence")


_FIELDS = {
    "task": {"base", "agent_material", "verifier_material"},
    "target": {"requested_identity", "observed_identity", "runtime"},
    "agent": {"harness", "configuration"},
    "condition": {"task", "target", "agent", "hosts", "track", "budgets", "cache_policy",
                  "capabilities", "observability", "required_semantics", "retry_policy"},
    "result": {"condition", "attempts"},
}
_PHASES = {"queue", "provisioning", "setup", "agent_work", "verification", "end_to_end"}


def validate_manifest(value: dict[str, Any]) -> dict[str, Any]:
    """Validate a v1 descriptor and return an independent copy; no I/O or scoring."""
    try:
        _json(value, "manifest")
    except RecursionError as exc:
        raise ManifestError("manifest: circular or excessively nested JSON") from exc
    item = _object(value, "manifest")
    kind = _choice(item.get("kind"), set(_FIELDS), "manifest.kind")
    _object(item, kind, _FIELDS[kind] | {"schema_version", "kind", "id", "revision", "provenance"})
    if type(item.get("schema_version")) is not int or item["schema_version"] != 1:
        raise ManifestError(f"{kind}.schema_version: supported integer version is 1")
    for name in ("id", "revision"):
        _text(item.get(name), f"{kind}.{name}")
    _provenance(item.get("provenance"), f"{kind}.provenance")
    if kind == "task":
        base = _object(item.get("base"), "task.base", {"uri", "sha256"})
        _text(base.get("uri"), "task.base.uri")
        _digest(base.get("sha256"), "task.base.sha256")
        materials: dict[str, list[str]] = {}
        digests: dict[str, set[str]] = {}
        for name, audience in (("agent_material", "requirement_only"), ("verifier_material", "verifier_only")):
            materials[name] = []
            digests[name] = set()
            for index, raw in enumerate(_array(item.get(name), f"task.{name}")):
                path = f"task.{name}[{index}]"
                material = _object(raw, path, {"uri", "sha256", "audience"})
                uri = _text(material.get("uri"), f"{path}.uri")
                _digest(material.get("sha256"), f"{path}.sha256")
                digests[name].add(material["sha256"])
                if material.get("audience") != audience:
                    raise ManifestError(f"{path}.audience: expected {audience}")
                materials[name].append(uri)
            if not materials[name] or len(set(materials[name])) != len(materials[name]):
                raise ManifestError(f"task.{name}: requires nonempty, unique material references")
        if set(materials["agent_material"]) & set(materials["verifier_material"]):
            raise ManifestError("task.agent_material: verifier URI cannot also be agent-facing")
        if digests["agent_material"] & digests["verifier_material"]:
            raise ManifestError("task.agent_material: verifier content digest cannot also be agent-facing")
    elif kind == "target":
        _text(item.get("requested_identity"), "target.requested_identity")
        for name in ("observed_identity", "runtime"):
            evidence = _evidence(item.get(name), f"target.{name}")
            if evidence["status"] == "known":
                _text(evidence["value"], f"target.{name}.value")
    elif kind == "agent":
        _reference(item.get("harness"), "agent.harness")
        _evidence(item.get("configuration"), "agent.configuration")
    elif kind == "condition":
        for name in ("task", "target", "agent"):
            _reference(item.get(name), f"condition.{name}")
        hosts = _object(item.get("hosts"), "condition.hosts", {"inference", "agent", "verifier"})
        for role in ("inference", "agent", "verifier"):
            evidence = _evidence(hosts.get(role), f"condition.hosts.{role}")
            if evidence["status"] == "known":
                _text(evidence["value"], f"condition.hosts.{role}.value")
        _choice(item.get("track"), {"practical_system", "controlled_capability", "harness_configuration"}, "condition.track")
        _choice(item.get("retry_policy"), {"no_automatic_retries", "declared_retries"}, "condition.retry_policy")
        budgets = _object(item.get("budgets"), "condition.budgets", {
            "active_safety_seconds", "response_tokens", "reasoning_tokens", "attempt_limit",
        })
        for name in ("active_safety_seconds", "response_tokens", "reasoning_tokens", "attempt_limit"):
            evidence = _evidence(budgets.get(name), f"condition.budgets.{name}")
            if evidence["status"] == "known":
                _number(evidence["value"], f"condition.budgets.{name}", integer=name != "active_safety_seconds")
                if name == "attempt_limit" and evidence["value"] < 1:
                    raise ManifestError("condition.budgets.attempt_limit: must allow at least one attempt")
        _evidence(item.get("cache_policy"), "condition.cache_policy")
        capabilities = _object(item.get("capabilities"), "condition.capabilities")
        for name, raw in capabilities.items():
            evidence = _evidence(raw, f"condition.capabilities.{name}")
            if evidence["status"] == "known" and type(evidence["value"]) is not bool:
                raise ManifestError(f"condition.capabilities.{name}: known capability must be boolean")
        for name, raw in _object(item.get("observability"), "condition.observability").items():
            _evidence(raw, f"condition.observability.{name}")
        required = _array(item.get("required_semantics"), "condition.required_semantics")
        for name in required:
            _text(name, "condition.required_semantics")
            evidence = capabilities.get(name)
            if evidence is None or evidence["status"] != "known" or evidence["value"] is not True:
                raise ManifestError(f"condition.required_semantics.{name}: required capability is not supported; supply evidence or change the condition")
        if len(set(required)) != len(required):
            raise ManifestError("condition.required_semantics: duplicate requirement")
    else:
        _reference(item.get("condition"), "result.condition")
        attempts = _array(item.get("attempts"), "result.attempts")
        if not attempts:
            raise ManifestError("result.attempts: every started trial requires attempt evidence")
        seen: set[str] = set()
        for index, raw in enumerate(attempts):
            path = f"result.attempts[{index}]"
            attempt = _object(raw, path, {"id", "retry_of", "verdict", "state", "stop_reason",
                                         "verifier", "events", "timing", "time_to_verified_completion", "usage"})
            attempt_id = _text(attempt.get("id"), f"{path}.id")
            if attempt_id in seen:
                raise ManifestError(f"{path}.id: duplicate attempt")
            if "retry_of" in attempt and _text(attempt["retry_of"], f"{path}.retry_of") not in seen:
                raise ManifestError(f"{path}.retry_of: must reference an earlier retained attempt")
            seen.add(attempt_id)
            verdict = _choice(attempt.get("verdict"), {"passed", "failed", "ungraded"}, f"{path}.verdict")
            state = _choice(attempt.get("state"), {"completed", "stopped", "interrupted"}, f"{path}.state")
            stop = _choice(attempt.get("stop_reason"), {
                "success", "agent_finished", "response_cap", "timeout", "interruption", "evaluator_error", "cancellation",
                "runtime_error", "infrastructure_error", "safety_stop",
            }, f"{path}.stop_reason")
            verifier = _object(attempt.get("verifier"), f"{path}.verifier", {"status", "independent", "source"})
            status = _choice(verifier.get("status"), {"passed", "failed", "not_run", "error"}, f"{path}.verifier.status")
            if type(verifier.get("independent")) is not bool:
                raise ManifestError(f"{path}.verifier.independent: expected boolean declaration")
            _text(verifier.get("source"), f"{path}.verifier.source")
            expected = {"passed": "passed", "failed": "failed", "not_run": "ungraded", "error": "ungraded"}[status]
            if verdict != expected or (verdict == "passed" and not verifier["independent"]):
                raise ManifestError(f"{path}.verdict: inconsistent with independent verifier status")
            if stop == "success" and (verdict != "passed" or state != "completed"):
                raise ManifestError(f"{path}.stop_reason: success requires completed, independently verified pass")
            if (state == "interrupted") != (stop == "interruption"):
                raise ManifestError(f"{path}.state: interruption requires explicit interrupted recovery state")
            if stop in {"response_cap", "timeout", "cancellation", "runtime_error", "infrastructure_error", "safety_stop"} and state != "stopped":
                raise ManifestError(f"{path}.state: {stop} requires stopped state")
            if stop == "evaluator_error" and status != "error":
                raise ManifestError(f"{path}.verifier: evaluator_error requires error status")
            for event in _array(attempt.get("events"), f"{path}.events"):
                event = _object(event, f"{path}.events", {"category", "code", "source"})
                _choice(event.get("category"), {"infrastructure", "safety", "runtime"}, f"{path}.events.category")
                for name in ("code", "source"):
                    _text(event.get(name), f"{path}.events.{name}")
            timing = _object(attempt.get("timing"), f"{path}.timing", _PHASES)
            for phase, measurement in timing.items():
                _timing(measurement, f"{path}.timing.{phase}", phase)
            end = timing.get("end_to_end")
            if end is not None and end["status"] == "known":
                for phase, measurement in timing.items():
                    if phase == "end_to_end" or measurement["status"] != "known":
                        continue
                    data, total = measurement["value"], end["value"]
                    clock_fields = ("clock", "host_ids", "correlation_id")
                    same_clock = all(data.get(key) == total.get(key) for key in clock_fields)
                    if (same_clock and measurement["source"] == end["source"]
                            and total["coverage"] == "complete" and data["seconds"] > total["seconds"]):
                        raise ManifestError(f"{path}.timing.{phase}: exceeds complete end-to-end duration on the same clock")
            if "time_to_verified_completion" in attempt:
                completion = attempt["time_to_verified_completion"]
                _timing(completion, f"{path}.time_to_verified_completion", "end_to_end")
                if completion["status"] == "known":
                    if verdict != "passed" or state != "completed" or stop != "success":
                        raise ManifestError(f"{path}.time_to_verified_completion: only independently verified success has completion time")
                    if completion["value"]["coverage"] != "complete" or completion != timing.get("end_to_end"):
                        raise ManifestError(f"{path}.time_to_verified_completion: requires the complete end-to-end measurement")
            for name, raw_usage in _object(attempt.get("usage"), f"{path}.usage").items():
                evidence = _evidence(raw_usage, f"{path}.usage.{name}")
                if evidence["status"] == "known":
                    _number(evidence["value"], f"{path}.usage.{name}")
    return deepcopy(item)


def manifest_reference(value: dict[str, Any]) -> dict[str, str]:
    """Hash validated canonical JSON, not files or a claimed provider identity."""
    item = validate_manifest(value)
    canonical = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {"id": item["id"], "revision": item["revision"],
            "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


def validate_bundle(
    *, task: dict[str, Any], target: dict[str, Any], agent: dict[str, Any],
    condition: dict[str, Any], result: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate exact frozen references; never coerce historical import envelopes."""
    values = {"task": task, "target": target, "agent": agent, "condition": condition}
    if result is not None:
        values["result"] = result
    bundle = {name: validate_manifest(value) for name, value in values.items()}
    for name, item in bundle.items():
        if item["kind"] != name:
            raise ManifestError(f"bundle.{name}.kind: expected {name}")
    for name in ("task", "target", "agent"):
        if bundle["condition"][name] != manifest_reference(bundle[name]):
            raise ManifestError(f"condition.{name}: incompatible id/revision/digest; freeze the supplied manifest")
    if result is not None and bundle["result"]["condition"] != manifest_reference(bundle["condition"]):
        raise ManifestError("result.condition: incompatible id/revision/digest")
    return bundle
