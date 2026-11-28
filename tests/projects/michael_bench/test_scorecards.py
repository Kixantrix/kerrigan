"""Scorecards are generated from verified records, compare latest versions and never pool local with cloud."""
from benchmarks.michael.matrix import generate, pooled
from benchmarks.michael.scorecards import generate as scorecards


def row(model, task, repeat, *, passed=True, time=10, deployment="cloud", condition="R3", modes=(), **extra):
    return {"task": task, "repeat": repeat, "model": model, "deployment_class": deployment,
            "condition": condition, "tool_host": "test", "round": "v3", "family": "Implement",
            "size": {"tier": "small"}, "resolved": passed, "completion_seconds": time if passed else None,
            "tokens": {"inputTokens": 100, "outputTokens": 10}, "cost": None, "peak_memory_bytes": None,
            "energy_joules": None, "failure_modes": list(modes), "condition_sha256": "a" * 64,
            "source_sha256": "b" * 64, "ledger_source": "synthetic", **extra}


def render(records):
    value = generate.build(records)
    value["pooled_routing"] = pooled.pooled(records)
    return scorecards.build(records, value, blind=(25, 0))


def test_scorecards_compare_latest_versions_and_disclose_selection_and_unknowns():
    records = [row("gemini-4-neon", "fixture-v2", r, time=5 + r) for r in range(1, 4)]
    records += [row("gemini-4-neon", "fixture", 1, passed=False, modes=["spec-misread"])]
    records += [row("claude-sonnet-5.5", "fixture-v2", r, passed=r != 2, modes=() if r != 2 else ["spec-misread"])
                for r in range(1, 4)]
    cards, table = render(records)
    gemini = cards["gemini-4-neon"]
    assert "3/3" in gemini and "spec-misread" not in gemini  # superseded v1 failure excluded
    assert "superseded versions excluded here (still in the matrix): fixture." in gemini
    assert "Selection role in admission" in gemini and "25 passed, 0 failed" in gemini
    assert "**pass^3:** 1/1 tasks" in gemini
    assert "unknown / unknown / unknown" in gemini
    sonnet = cards["claude-sonnet-5.5"]
    assert "`spec-misread` | 1 | fixture-v2 repeat 2 (R3)" in sonnet
    assert "| [Gemini 4 Neon](gemini-4-neon.md) | cloud | 3/3" in table
    assert table.index("Claude Sonnet 5.5") < table.index("Gemini 4 Neon")


def test_local_scorecard_is_separate_and_excludes_sleep_timing():
    records = [row("claude-sonnet-5.5", "fixture", r) for r in range(1, 4)]
    local = "mtplx-inkling-2-mini-optimized-quality"
    records += [row(local, "fixture", 1, time=500, deployment="local laptop", condition="L/v9d",
                    timing_excluded="host-sleep"),
                row(local, "fixture", 2, time=40, deployment="local laptop", condition="L/v9d")]
    cards, table = render(records)
    assert "local laptop" in cards[local] and "never pooled with cloud" in cards[local]
    assert "median [IQR] 40s; 1 host-sleep timing(s) excluded" in cards[local]
    assert "| [Inkling-2-mini (local)](" + local + ".md) | local laptop | 2/2" in table


def test_committed_scorecards_match_generation():
    records, _ = generate.default_records()
    value = generate.build(records)
    value["pooled_routing"] = pooled.pooled(records)
    cards, table = scorecards.build(records, value, scorecards.blind_record(
        generate.ROOT / "benchmarks/michael/curriculum"))
    assert (scorecards.HERE / "overview.md").read_text() == table
    for model, text in cards.items():
        assert (scorecards.HERE / f"{model}.md").read_text() == text


def test_anchors_never_feed_routing_and_report_raw_and_adjusted():
    rows = [row("gpt-6.2-astra", "fixture", r) for r in range(1, 4)]
    anchors = [row("gpt-6.2-astra", "anchor-x", r, passed=r != 3,
                   modes=() if r != 3 else ["anchor-overspecified"]) for r in range(1, 4)]
    for a in anchors:
        a["family"] = generate.ANCHOR_FAMILY
    records = rows + anchors
    value = generate.build(records)
    assert value["recommendations"]["Public anchor × small"]["status"] == "not routed (public anchor)"
    assert all(not column.startswith("Public anchor") for column in pooled.pooled(records)["recommendations"])
    cards, table = render(records)
    card = cards["gpt-6.2-astra"]
    assert "**Overall:** 3/3" in card  # anchors stay out of the overall rate
    assert "**Raw (upstream-comparable):** 2/3" in card and "**Adjusted:** 2/2" in card
    assert "| 2/3 / 2/2 |" in table and "host-resource-unavailable" in table
