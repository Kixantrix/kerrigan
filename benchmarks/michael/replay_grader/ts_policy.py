"""Trusted translation of the frozen grouping (4+2) and status (32+8) vitest cases.

Each row keeps one original vitest full name; clauses keep its expectations.
Only call inputs cross the sandbox boundary, never clauses or original names.
"""

DASH = "apps/kerrigan-dashboard/src"
GROUPING = f"{DASH}/components/StageDetailPanel/groupStageItems.ts"
STATUS = f"{DASH}/lib/status.ts"
TIME = "2026-01-01T00:00:00Z"


def _call(module, fn, *args):
    return {"module": module, "fn": fn, "args": list(args)}


def grouping_rows():
    def issue(**kw):
        return {"number": 1, "title": "M3.4: issue", "state": "open", "user": {"login": "agent"},
                "created_at": TIME, "updated_at": TIME, "labels": [],
                "html_url": "https://github.com/o/r/issues/1", **kw}

    def pr(**kw):
        return {"number": 2, "title": "M3.4: PR", "state": "open", "draft": False,
                "user": {"login": "agent"}, "created_at": TIME, "updated_at": TIME,
                "merged_at": None, "head": {"ref": "feature/m3-4", "sha": "abc123"},
                "base": {"ref": "main"}, "html_url": "https://github.com/o/r/pull/2", **kw}

    rows = []

    def add(group, name, calls, clauses):
        rows.append({"original_id": name, "group": group, "probe": {"calls": calls},
                     "clauses": clauses})

    parse = lambda title: _call(GROUPING, "parseSubMilestoneId", title)
    group = lambda *args: _call(GROUPING, "groupStageItemsBySubMilestone", *args)
    add("preservation", "parseSubMilestoneId parses canonical milestone tokens from titles",
        [parse("M3.4: dashboard work"), parse("feat: m2.10 follow-up")],
        [("path_equal", [0, "result"], "M3.4"), ("path_equal", [1, "result"], "M2.10")])
    add("preservation", "parseSubMilestoneId returns null when no sub-milestone token is present",
        [parse("M3 milestone tracking"), parse("general cleanup")],
        [("path_equal", [0, "result"], None), ("path_equal", [1, "result"], None)])
    add("preservation", "groupStageItemsBySubMilestone sorts sub-milestone groups by minor number "
        "and keeps issues plus PRs together",
        [group([issue(number=11, title="M3.10: issue"), issue(number=12, title="M3.2: issue")],
               [pr(number=21, title="M3.2: PR"), pr(number=22, title="M3.10: PR")])],
        [("path_equal", [0, "result", "*", "label"], ["M3.2", "M3.10"]),
         ("path_match", [0, "result", 0], {"label": "M3.2", "issues": [{"number": 12}],
                                            "prs": [{"number": 21}]}),
         ("path_match", [0, "result", 1], {"label": "M3.10", "issues": [{"number": 11}],
                                            "prs": [{"number": 22}]})])
    other_issue, other_pr = issue(number=31, title="Milestone tracking issue"), pr(number=41, title="fix(dashboard): polish")
    add("preservation", "groupStageItemsBySubMilestone places unmatched items into an Other bucket",
        [group([other_issue], [other_pr])],
        [("path_match", [0, "result"], [{"id": None, "label": "Other", "issues": [{"number": 31}],
                                         "prs": [{"number": 41}]}]),
         ("path_keys", [0, "result", 0], ["id", "issues", "label", "prs"])])
    issues, prs = [{"number": 1, "title": "M2.1 foreign"}], [{"number": 2, "title": "M4.2 foreign"}]
    add("regression", "current-major grouping regression places foreign-only issues and PRs in Other",
        [group(issues, prs, 3)],
        [("path_equal", [0, "result"], [{"id": None, "label": "Other", "issues": issues, "prs": prs}])])
    issues = [{"title": "M2.1 then m3.10"}, {"title": "M4.7 then M3.2"}]
    prs = [{"title": "M2.4 then M3.2 then M3.1"}]
    add("regression", "current-major grouping regression selects current references after foreign "
        "references and sorts numerically",
        [group(issues, prs, 3), parse("M2.1 then M3.10")],
        [("path_equal", [0, "result", "*", "id"], ["M3.2", "M3.10"]),
         ("path_equal", [0, "result", 0, "issues"], [issues[1]]),
         ("path_equal", [0, "result", 0, "prs"], prs),
         ("path_equal", [0, "mutated"], False),
         ("path_equal", [1, "result"], "M2.1")])
    return rows


def status_rows():
    def pr(**kw):
        return {"number": 1, "title": "M3.2 status work", "state": "open", "draft": False,
                "user": {"login": "agent"}, "created_at": TIME, "updated_at": TIME,
                "head": {"ref": "feature", "sha": "abc123"}, "base": {"ref": "main"},
                "html_url": "https://example.com/pr/1", **kw}

    def issue(**kw):
        return {"number": 1, "title": "M3.2 issue", "state": "open", "user": {"login": "agent"},
                "created_at": TIME, "updated_at": TIME, "labels": [],
                "html_url": "https://example.com/issues/1", **kw}

    def review(**kw):
        return {"id": 1, "user": {"login": "reviewer"}, "state": "COMMENTED", "submitted_at": TIME,
                "body": "lgtm", "html_url": "https://example.com/reviews/1", **kw}

    def stage(id_, label):
        return {"id": id_, "label": label, "level": 2, "parentId": None}

    graph = lambda *nodes: {"nodes": list(nodes), "edges": []}
    go = [{"name": "agent:go"}]
    rows = []

    def add(group, name, calls, clauses):
        rows.append({"original_id": name, "group": group, "probe": {"calls": calls},
                     "clauses": clauses})

    derive = lambda value: _call(STATUS, "deriveStageStatus", value)
    statuses = lambda g, value: _call(STATUS, "deriveStatuses", g, value)
    matcher = lambda s, item: _call(STATUS, "defaultStageMatcher", s, item)
    by_stage = lambda *args: _call(STATUS, "groupPRsByStage", *args)
    work = lambda g, value: _call(STATUS, "groupStageWorkByStage", g, value)
    result = lambda index=0: [index, "result"]
    entry = lambda key, index=0: [index, "result", "$map", key]

    for name, value, expected in [
        ("planned", {"prs": [], "issues": [], "blocks": []}, "planned"),
        ("dispatched", {"prs": [pr()], "issues": [issue(labels=go)], "blocks": [],
                        "reviewsByPr": {"$map": [[1, []]]}}, "dispatched"),
        ("in-review", {"prs": [pr()], "issues": [issue(labels=go)], "blocks": [],
                       "reviewsByPr": {"$map": [[1, [review(state="CHANGES_REQUESTED")]]]}}, "in-review"),
        ("blocked", {"prs": [pr()], "issues": [issue(labels=go)], "blocks": [{"open": True}]}, "blocked"),
        ("needs-attestation", {"prs": [], "issues": [issue(labels=[{"name": "agent:needs-attestation"}])],
                               "blocks": []}, "needs-attestation"),
        ("needs-human-test", {"prs": [], "issues": [issue(labels=[{"name": "agent:needs-human-test"}])],
                              "blocks": []}, "needs-human-test"),
        ("merged", {"prs": [pr(state="merged")], "issues": [], "blocks": []}, "merged"),
        ("merged via merged_at field", {"prs": [pr(state="closed", merged_at="2026-02-01T00:00:00Z")],
                                        "issues": [], "blocks": []}, "merged"),
    ]:
        add("preservation", f"deriveStageStatus returns {name}", [derive(value)],
            [("path_equal", result(), expected)])
    add("preservation", "deriveStageStatus applies precedence when multiple signals are present",
        [derive({"prs": [pr()], "issues": [issue(labels=go),
                                           issue(number=2, labels=[{"name": "agent:needs-attestation"}])],
                 "blocks": [{"open": True}],
                 "reviewsByPr": {"$map": [[1, [review(state="CHANGES_REQUESTED")]]]}})],
        [("path_equal", result(), "blocked")])
    add("preservation", "deriveStageStatus returns planned for empty input",
        [derive({"prs": [], "issues": [], "blocks": []})], [("path_equal", result(), "planned")])
    add("preservation", "deriveStageStatus closed issue without open PR does not trigger dispatched",
        [derive({"prs": [], "issues": [issue(state="closed", labels=go)], "blocks": []})],
        [("path_equal", result(), "planned")])
    add("preservation", "deriveStageStatus closed PR without merged_at does not trigger merged",
        [derive({"prs": [pr(state="closed", merged_at=None)], "issues": [], "blocks": []})],
        [("path_equal", result(), "planned")])

    add("preservation", "deriveStatuses aggregates matched multi-repo items by highest precedence",
        [statuses(graph(stage("m3-2", "M3.2 Status")), {
            "prs": [pr(number=1, title="repo-a: M3.2 open"),
                    pr(number=2, title="repo-b: M3.2 merged", state="merged")],
            "issues": [issue(title="repo-a: M3.2 issue", labels=go)],
            "blocks": [{"open": True, "title": "repo-b: M3.2 blocker"}]})],
        [("path_equal", entry("m3-2"), "blocked")])
    add("preservation", "deriveStatuses supports an injectable matcher",
        [statuses(graph(stage("alpha", "Alpha")), {
            "prs": [pr(title="[ALPHA] implementation")],
            "issues": [issue(title="[ALPHA] tracking", labels=go)], "blocks": [],
            "matcher": {"$fn": "bracketUpperId"}})],
        [("path_equal", entry("alpha"), "dispatched")])
    m51 = graph(stage("m5-1", "M5.1 Ship feature"))
    m51_input = {"prs": [pr(number=10, title="M5.1 ship feature", state="closed",
                            merged_at="2026-05-01T00:00:00Z")], "issues": [], "blocks": []}
    add("preservation", "deriveStatuses shows merged when the stage has a merged PR (via merged_at) "
        "and no open work", [statuses(m51, m51_input)], [("path_equal", entry("m5-1"), "merged")])

    m32 = stage("m3-2", "Status taxonomy")
    dag = stage("m3-project-detail-dag", "Project Detail DAG")
    add("preservation", "defaultStageMatcher matches titles containing a normalized stage id",
        [matcher(m32, {"title": "Task M3.2: status taxonomy"})], [("path_equal", result(), True)])
    add("preservation", "defaultStageMatcher matches via milestone prefix for heading-derived ids "
        "(e.g. m3-project-detail-dag → M3)",
        [matcher(dag, {"title": t}) for t in ("M3 tracking issue", "feat: M3.1 ship it", "fix M3.4 bug")],
        [("path_equal", result(i), True) for i in range(3)])
    add("preservation", "defaultStageMatcher does not match M30 when milestone prefix is m3",
        [matcher(dag, {"title": t}) for t in ("M30 unrelated milestone", "feat M31 unrelated")],
        [("path_equal", result(i), False) for i in range(2)])
    add("preservation", "defaultStageMatcher does NOT match via body-only milestone mention "
        "(false-positive prevention)",
        [matcher(dag, {"title": "fix: some hotfix with no milestone in title"})],
        [("path_equal", result(), False)])
    add("preservation", "defaultStageMatcher matches via milestone prefix in head branch ref",
        [matcher(dag, {"title": "fix: hotfix", "head": {"ref": "feature/m3-dag-polish"}})],
        [("path_equal", result(), True)])
    sub = stage("m3-2", "M3.2 status taxonomy")
    add("preservation", "defaultStageMatcher does not apply milestone-prefix matching to sub-indexed "
        "stages (m3-2, m3-4-some-feature)",
        [matcher(sub, {"title": "Task M3.2: status taxonomy"}), matcher(sub, {"title": "M3.4 unrelated sub-task"})],
        [("path_equal", result(0), True), ("path_equal", result(1), False)])

    tracking = lambda merged, title, **kw: {"prs": [], "issues": [issue(
        title="M3 tracking issue", state="closed",
        closingPRs=[{"number": 42, "merged": merged, "title": title, "url": "https://example.com/pr/42"}])],
        "blocks": [], **kw}
    prefix = "deriveStatuses — closing-PR traversal (Option C) "
    add("preservation", prefix + "shows merged when a matched issue was closed by a merged PR even if "
        "PR title lacks milestone",
        [statuses(graph(dag), tracking(True, "fix(dashboard): some unrelated title"))],
        [("path_equal", entry("m3-project-detail-dag"), "merged")])
    add("preservation", prefix + "shows planned when the closing PR of a matched issue was NOT merged "
        "(only closed)", [statuses(graph(dag), tracking(False, "fix: closed without merge"))],
        [("path_equal", entry("m3-project-detail-dag"), "planned")])
    add("preservation", prefix + "blocked takes precedence over closing-PR merged signal",
        [statuses(graph(dag), tracking(True, "fix: merged hotfix",
                                       blocks=[{"open": True, "title": "M3 blocker"}]))],
        [("path_equal", entry("m3-project-detail-dag"), "blocked")])
    add("preservation", prefix + "direct merged-PR title match (#385) still works alongside "
        "closing-PR traversal", [statuses(m51, m51_input)], [("path_equal", entry("m5-1"), "merged")])

    two = graph(stage("m3-2", "M3.2 Status"), stage("m3-3", "M3.3 DAG"))
    add("preservation", "groupPRsByStage returns an empty map when no PRs are provided",
        [by_stage(two, [])], [("path_equal", [0, "result", "$map"], {})])
    matched = pr(number=1, title="M3.2 status work")
    add("preservation", "groupPRsByStage maps a PR to the correct stage", [by_stage(two, [matched])],
        [("path_equal", entry("m3-2"), [matched]), ("path_absent", entry("m3-3"))])
    a1 = pr(number=1, title="M3.2 open PR", html_url="https://github.com/o/r/pull/1")
    a2 = pr(number=2, title="M3.2 merged PR", state="closed", merged_at="2026-05-01T00:00:00Z",
            html_url="https://github.com/o/r/pull/2")
    b1 = pr(number=3, title="M3.3 dag work", html_url="https://github.com/o/r/pull/3")
    add("preservation", "groupPRsByStage groups multiple PRs across multiple stages",
        [by_stage(two, [a1, a2, b1])],
        [("path_equal", entry("m3-2"), [a1, a2]), ("path_equal", entry("m3-3"), [b1])])
    add("preservation", "groupPRsByStage does not include stages that have no matching PRs",
        [by_stage(two, [pr(number=99, title="chore: unrelated change",
                           html_url="https://github.com/o/r/pull/99")])],
        [("path_absent", entry("m3-2")), ("path_absent", entry("m3-3"))])
    single = pr(number=5, title="anything", html_url="https://github.com/o/r/pull/5")
    add("preservation", "groupPRsByStage supports a custom matcher override",
        [by_stage(two, [single], {"$fn": "always"})],
        [("path_equal", entry("m3-2"), [single]), ("path_equal", entry("m3-3"), [single])])

    m3 = graph(stage("m3", "M3"))
    tracked = issue(number=24, title="M3.4: tracking issue")
    direct = pr(number=42, title="M3.4 status work", html_url="https://github.com/o/r/pull/42")
    add("preservation", "groupStageWorkByStage groups matched issues and PRs together for a stage",
        [work(m3, {"prs": [direct], "issues": [tracked]})],
        [("path_equal", entry("m3"), {"prs": [direct], "issues": [tracked]})])
    direct = pr(number=88, title="fix(dashboard): detail panel polish", state="closed",
                merged_at="2026-05-01T00:00:00Z", head={"ref": "feature/m3-4-polish", "sha": "abc123"},
                html_url="https://github.com/o/r/pull/88")
    tracked = issue(title="M3.4: tracking issue", closingPRs=[
        {"number": 88, "merged": True, "title": "fix(dashboard): detail panel polish",
         "url": "https://github.com/o/r/pull/88"},
        {"number": 89, "merged": True, "title": "fix(dashboard): follow-up",
         "url": "https://github.com/o/r/pull/89"}])
    add("preservation", "groupStageWorkByStage includes merged closing PRs for matched issues without "
        "duplicating direct matches", [work(m3, {"prs": [direct], "issues": [tracked]})],
        [("path_equal", entry("m3") + ["issues"], [tracked]),
         ("path_equal", entry("m3") + ["prs", 0], direct),
         ("path_match", entry("m3") + ["prs"], [{}, {"number": 89, "title": "fix(dashboard): follow-up",
                                                     "state": "merged",
                                                     "html_url": "https://github.com/o/r/pull/89"}])])

    node = graph({"id": "M3.2", "label": "M3.2 work", "level": 2, "parentId": None})
    merged_pr = lambda title, number=1: {"number": number, "title": title, "state": "merged",
                                         "merged_at": "2026-01-01", "html_url": f"https://example.com/pr/{number}",
                                         "head": {"ref": "feature"}}
    prefix = "implementation-only stage work regression "
    for title in ["docs: M3.2 guide", "plan: M3.2 work", " DOCS(api): M3.2 ", "plan(build): M3.2",
                  "chore(briefings): M3.2", "docs(briefings): M3.2"]:
        value = {"prs": [merged_pr(title)], "issues": [], "blocks": []}
        add("regression", prefix + f"excludes nonimplementation PR {title}",
            [work(node, value), statuses(node, value)],
            [("path_equal", [0, "result", "$map"], {}), ("path_equal", entry("M3.2", 1), "planned")])
    value = {"prs": [], "blocks": [], "issues": [{"title": "M3.2 issue", "state": "closed", "labels": [],
             "closingPRs": [{"number": 1, "title": "docs: M3.2 guide", "merged": True,
                             "url": "https://example.com/pr/1"}]}]}
    add("regression", prefix + "excludes documentation closing references but retains issue association",
        [work(node, value), statuses(node, value)],
        [("path_equal", entry("M3.2") + ["prs"], []), ("path_equal", entry("M3.2", 1), "planned")])
    real = merged_pr("feat: M3.2 implementation", 2)
    value = {"prs": [merged_pr("docs: M3.2 guide"), real, real], "issues": [], "blocks": []}
    add("regression", prefix + "preserves mixed implementation work and deduplication",
        [work(node, value), statuses(node, value)],
        [("path_equal", entry("M3.2") + ["prs"], [real]), ("path_equal", entry("M3.2", 1), "merged")])
    return rows
