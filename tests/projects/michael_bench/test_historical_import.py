"""AC-MB-001 / partial AC-MB-003: integration, cloud-linux, synthetic only."""

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

CONTRACTS = Path(__file__).resolve().parents[3] / "benchmarks" / "michael" / "contracts"
sys.path.insert(0, str(CONTRACTS))
from historical_import import HistoricalImportError, import_historical


@pytest.fixture
def source():
    return (CONTRACTS / "fixtures" / "pilot-v1.json").read_bytes()


def digest(source):
    return hashlib.sha256(source).hexdigest()


def correction(source):
    return {
        "id": "stop-correction-1",
        "source_sha256": digest(source),
        "attempt_id": "failed",
        "field": "stop_reason",
        "original_value": "stop",
        "corrected_value": "response_cap",
        "provenance": {"source_id": "synthetic-correction", "reason": "native cap receipt"},
        "extra_evidence": {"retained": True},
    }


def test_historical_import_preserves_evidence(source):
    corrections = [correction(source)]
    original = deepcopy(corrections)
    record = import_historical(source, expected_sha256=digest(source), corrections=corrections)
    assert base64.b64decode(record["source"]["bytes_base64"]) == source
    assert record["source"]["sha256"] == digest(source)
    assert record["source"]["payload"] == json.loads(source)
    assert (CONTRACTS / "fixtures" / "pilot-v1.json").read_bytes() == source
    assert record["source"]["payload"]["attempts"][0]["stop_reason"] == "stop"
    assert record["corrections"] == original == corrections
    assert record["schema_version"] == 1
    assert record["status"] == "historical"
    for name in ("task", "target", "condition", "provenance"):
        assert record[name] == json.loads(source)[name]
    assert record == import_historical(source, expected_sha256=digest(source), corrections=corrections)
    corrections[0]["provenance"]["reason"] = "caller mutation"
    record["condition"]["response_cap"] = 999
    assert record["corrections"] == original
    assert record["source"]["payload"]["condition"]["response_cap"] == 100


def test_corrections_are_additive_records(source):
    first = import_historical(source, expected_sha256=digest(source))
    snapshot = deepcopy(first)
    amended = import_historical(source, expected_sha256=digest(source), corrections=[correction(source)])
    assert first == snapshot
    assert first["record_id"] != amended["record_id"]
    assert first["source"] == amended["source"]
    assert first["corrections"] == []


def test_byte_distinct_sources_remain_distinct(source):
    padded = source + b" \n"
    first = import_historical(source, expected_sha256=digest(source))
    second = import_historical(padded, expected_sha256=digest(padded))
    assert first["source"]["payload"] == second["source"]["payload"]
    assert first["record_id"] != second["record_id"]
    assert base64.b64decode(second["source"]["bytes_base64"]) == padded


def test_unavailable_usage_and_rail_power_are_not_invented(source):
    payload = json.loads(source)
    payload["condition"] = {"id": "finite-power-only", "track": "power-only"}
    payload["usage"] = {"kind": "not_applicable", "cache": "not_applicable"}
    payload["telemetry"] = {"watts": 4.5, "scope": "soc_rail", "whole_device_watts": None}
    raw = json.dumps(payload).encode()
    imported = import_historical(raw, expected_sha256=digest(raw))["source"]["payload"]
    assert imported == payload
    assert [attempt.get("usage", {}).get("kind") for attempt in imported["attempts"]] == [
        "native", "unknown", "derived", None,
    ]
    assert imported["attempts"][3]["verdict"] == "ungraded"
    assert imported["attempts"][3]["telemetry"]["watts"] is None
    assert imported["usage"]["cache"] == "not_applicable"
    assert imported["telemetry"]["scope"] == "soc_rail"
    assert imported["telemetry"]["whole_device_watts"] is None


@pytest.mark.parametrize("raw", [
    b"", b"\xff", b"{", b"[]", b"null",
    b'{"schema_version": 1, "schema_version": 1}',
    b'{"unknown": NaN}', b'{"unknown": Infinity}', b'{"unknown": 1e999}',
    b'{"unknown": ' + b"1" * 5000 + b'}',
])
def test_invalid_json_is_explicit(raw):
    with pytest.raises(HistoricalImportError, match="source"):
        import_historical(raw, expected_sha256=digest(raw))


@pytest.mark.parametrize("field,value", [
    ("schema_version", 2), ("schema_version", True), ("schema_version", "1"),
    ("task", None), ("target", {"id": ""}), ("condition", []),
    ("provenance", {}), ("attempts", {}), ("attempts", [{"id": 1}]),
    ("denominators", None),
])
def test_invalid_source_contract(source, field, value):
    payload = json.loads(source)
    payload[field] = value
    raw = json.dumps(payload).encode()
    with pytest.raises(HistoricalImportError, match=field):
        import_historical(raw, expected_sha256=digest(raw))


@pytest.mark.parametrize("change", ["missing", "duplicate", "bad-retry"])
def test_missing_or_inconsistent_source_fields(source, change):
    payload = json.loads(source)
    if change == "missing":
        del payload["denominators"]
    elif change == "duplicate":
        payload["attempts"][1]["id"] = "failed"
    else:
        payload["attempts"][2]["retry_of"] = "absent"
    raw = json.dumps(payload).encode()
    with pytest.raises(HistoricalImportError):
        import_historical(raw, expected_sha256=digest(raw))


@pytest.mark.parametrize("field,value", [
    ("id", ""), ("source_sha256", "invalid"), ("source_sha256", "0" * 64),
    ("attempt_id", "absent"), ("field", "verdict"), ("original_value", "wrong"),
    ("corrected_value", None), ("provenance", {}), ("extra_evidence", float("nan")),
])
def test_inconsistent_corrections(source, field, value):
    amendment = correction(source)
    amendment[field] = value
    with pytest.raises(HistoricalImportError, match="corrections"):
        import_historical(source, expected_sha256=digest(source), corrections=[amendment])


def test_invalid_arguments_and_duplicate_corrections(source):
    for expected in (None, 123, "bad", "0" * 64, digest(source).upper()):
        with pytest.raises(HistoricalImportError, match="SHA-256"):
            import_historical(source, expected_sha256=expected)
    with pytest.raises(HistoricalImportError, match="bytes"):
        import_historical(source.decode(), expected_sha256=digest(source))
    for amendments in ({}, [None], [correction(source), correction(source)]):
        with pytest.raises(HistoricalImportError, match="corrections"):
            import_historical(source, expected_sha256=digest(source), corrections=amendments)


def test_non_json_correction_values_are_explicit(source):
    for value in ((1, 2), {1: "non-string key"}, object()):
        amendment = correction(source)
        amendment["extra_evidence"] = value
        with pytest.raises(HistoricalImportError, match="corrections"):
            import_historical(source, expected_sha256=digest(source), corrections=[amendment])
    amendment = correction(source)
    amendment["extra_evidence"] = amendment
    with pytest.raises(HistoricalImportError, match="corrections"):
        import_historical(source, expected_sha256=digest(source), corrections=[amendment])
