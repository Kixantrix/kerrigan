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
        "failure_modes": [] if passed else ["unsupported defect claim"],
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
    assert cell["failure_modes"] == ["unsupported defect claim"]
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
