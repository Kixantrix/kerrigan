"""Engine-neutral, lossless historical import v1; no filesystem or runtime access."""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import math
import re
from typing import Any


class HistoricalImportError(ValueError):
    """An invalid import, with the offending field or source in the message."""


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HistoricalImportError(f"{path}: expected an object")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HistoricalImportError(f"{path}: expected a nonempty string")
    return value


def _digest(value: Any, path: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise HistoricalImportError(f"{path}: expected a lowercase 64-character SHA-256")
    return value


def _json_values(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise HistoricalImportError(f"{path}: JSON object keys must be strings")
            _json_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _json_values(child, f"{path}[{index}]")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise HistoricalImportError(f"{path}: JSON numbers must be finite")
    elif value is not None and not isinstance(value, (str, int, bool)):
        raise HistoricalImportError(f"{path}: expected a JSON value")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HistoricalImportError(f"source: duplicate JSON key {key!r}")
        result[key] = value
    return result


def import_historical(
    source_bytes: bytes,
    *,
    expected_sha256: str,
    corrections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate a synthetic/sanitized v1 pilot and return a new historical envelope.

    The caller supplies the independently expected digest. Corrections annotate
    original stop reasons; they never patch the payload. Persistence is caller-owned.
    """
    if not isinstance(source_bytes, bytes):
        raise HistoricalImportError("source: expected immutable UTF-8 JSON bytes")
    expected = _digest(expected_sha256, "expected_sha256")
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != expected:
        raise HistoricalImportError(f"source SHA-256 mismatch: expected {expected}, got {actual}")
    try:
        payload = json.loads(source_bytes.decode("utf-8"), object_pairs_hook=_unique_object)
        _json_values(payload, "source")
    except HistoricalImportError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise HistoricalImportError(f"source: invalid UTF-8 JSON ({exc})") from exc
    payload = _object(payload, "source")
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        raise HistoricalImportError("source.schema_version: expected supported integer version 1")
    for name in ("task", "target", "condition", "provenance"):
        descriptor = _object(payload.get(name), f"source.{name}")
        key = "source_id" if name == "provenance" else "id"
        _text(descriptor.get(key), f"source.{name}.{key}")
    _object(payload.get("denominators"), "source.denominators")
    attempts = payload.get("attempts")
    if not isinstance(attempts, list):
        raise HistoricalImportError("source.attempts: expected an array")
    by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(attempts):
        path = f"source.attempts[{index}]"
        attempt = _object(value, path)
        attempt_id = _text(attempt.get("id"), f"{path}.id")
        if attempt_id in by_id:
            raise HistoricalImportError(f"{path}.id: duplicate attempt {attempt_id!r}")
        if "retry_of" in attempt:
            retry_id = _text(attempt["retry_of"], f"{path}.retry_of")
            if retry_id not in by_id:
                raise HistoricalImportError(f"{path}.retry_of: must reference an earlier attempt")
        by_id[attempt_id] = attempt
    amendments = [] if corrections is None else corrections
    if not isinstance(amendments, list):
        raise HistoricalImportError("corrections: expected an array")
    try:
        _json_values(amendments, "corrections")
    except RecursionError as exc:
        raise HistoricalImportError("corrections: circular or excessively nested JSON") from exc
    correction_ids: set[str] = set()
    for index, value in enumerate(amendments):
        path = f"corrections[{index}]"
        amendment = _object(value, path)
        correction_id = _text(amendment.get("id"), f"{path}.id")
        if correction_id in correction_ids:
            raise HistoricalImportError(f"{path}.id: duplicate correction {correction_id!r}")
        correction_ids.add(correction_id)
        if _digest(amendment.get("source_sha256"), f"{path}.source_sha256") != actual:
            raise HistoricalImportError(f"{path}.source_sha256: does not reference this source")
        attempt_id = _text(amendment.get("attempt_id"), f"{path}.attempt_id")
        if attempt_id not in by_id:
            raise HistoricalImportError(f"{path}.attempt_id: unknown attempt {attempt_id!r}")
        if amendment.get("field") != "stop_reason":
            raise HistoricalImportError(f"{path}.field: v1 supports only additive stop_reason corrections")
        attempt = by_id[attempt_id]
        original = _text(amendment.get("original_value"), f"{path}.original_value")
        if "stop_reason" not in attempt or original != attempt["stop_reason"]:
            raise HistoricalImportError(f"{path}.original_value: differs from original source stop_reason")
        _text(amendment.get("corrected_value"), f"{path}.corrected_value")
        provenance = _object(amendment.get("provenance"), f"{path}.provenance")
        _text(provenance.get("source_id"), f"{path}.provenance.source_id")
    record = {
        "schema_version": 1,
        "record_type": "historical_evidence",
        "status": "historical",
        **{name: deepcopy(payload[name]) for name in ("task", "target", "condition", "provenance")},
        "source": {
            "sha256": actual,
            "bytes_base64": base64.b64encode(source_bytes).decode("ascii"),
            "payload": payload,
        },
        "corrections": deepcopy(amendments),
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
    record["record_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return record
