"""Answer-free sandbox adapter: normalizes the candidate BRIEFING.json. Output is untrusted."""

import json
import re
from pathlib import Path

app = Path(__file__).resolve().parent
LEVELS = {"unit", "integration", "smoke", "e2e", "scenario"}


def text(value):
    return value.strip() if isinstance(value, str) else None


def ac_id(value):
    value = (text(value) or "").upper()
    return value[3:] if value.startswith("AC-") else value


def clean_path(value):
    value = (text(value) or "").strip("`").strip()
    return value[2:] if value.startswith("./") else value


def strings(value):
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def expand(glob):
    match = re.search(r"\{([^{}]*)\}", glob)
    if not match:
        return [glob]
    return [variant for option in match.group(1).split(",")
            for variant in expand(glob[:match.start()] + option + glob[match.end():])]


def compile_glob(glob):
    glob = clean_path(glob)
    if not glob:
        return None
    if glob.endswith("/"):
        glob += "**"
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    wild = any(ch in glob for ch in "*?")
    return re.compile(out + ("" if wild else "(?:/.*)?") + r"\Z")


def matcher(globs):
    patterns = [pattern for glob in globs for variant in expand(glob)
                if (pattern := compile_glob(variant)) is not None]
    return lambda path: any(pattern.match(path) for pattern in patterns)


def normalize(brief, probe):
    touched = matcher(strings(brief.get("touch")))
    if probe.get("op") == "match":
        return {"matched": sorted(path for path in probe["paths"] if touched(path))}
    acs = [item for item in brief.get("acceptance_criteria") or [] if isinstance(item, dict)]
    ids = [ac_id(item.get("id")) for item in acs]
    tests = {ac_id(item.get("id")): sorted({clean_path(t) for t in strings(item.get("tests")) if clean_path(t)})
             for item in acs}
    if probe.get("op") == "tests_under":
        listed = tests.get(probe["id"], [])
        return {"count": len(listed),
                "all": bool(listed) and all(t.startswith(probe["prefix"]) and t.endswith(probe["suffix"])
                                            for t in listed)}
    levels = {ac_id(item.get("id")): (text(item.get("level")) or "").lower() or None for item in acs}
    envs = {ac_id(item.get("id")): (text(item.get("environment")) or "").lower() or None for item in acs}
    deferred = [ac_id(item) for item in strings(brief.get("deferred_acs"))]
    opened = [(text(item) or "").upper() for item in strings(brief.get("open_owner_decisions"))]
    scope = brief.get("scope_items") if isinstance(brief.get("scope_items"), dict) else {}
    scope_in = [text(item) for item in strings(scope.get("in"))]
    scope_out = [text(item) for item in strings(scope.get("out"))]
    all_tests = sorted({t for listed in tests.values() for t in listed})
    return {
        "acs": sorted(set(ids)), "ac_dups": sorted({i for i in ids if ids.count(i) > 1}),
        "deferred": sorted(set(deferred)), "deferred_dups": sorted({i for i in deferred if deferred.count(i) > 1}),
        "reason": text(brief.get("deferred_reason")), "open": sorted(set(opened)),
        "routing": text(brief.get("routing_rule")),
        "level": levels, "env": envs, "tests": tests,
        "levels_used": sorted({str(v) for v in levels.values()}),
        "levels_outside": sorted(i for i, v in levels.items() if v not in LEVELS),
        "envs_used": sorted({str(v) for v in envs.values()}),
        "acs_without_tests": sorted(i for i, listed in tests.items() if not listed),
        "untouched_tests": [t for t in all_tests if not touched(t)],
        "scope_in": sorted(set(scope_in)), "scope_out": sorted(set(scope_out)),
        "scope_all": sorted(set(scope_in) | set(scope_out)),
        "scope_overlap": sorted(set(scope_in) & set(scope_out)),
        "scope_dups": sorted({i for i in scope_in + scope_out if (scope_in + scope_out).count(i) > 1}),
    }


probes = json.loads((app / "probes.json").read_text())
try:
    brief = json.loads((app / "BRIEFING.json").read_text(encoding="utf-8"))
    if not isinstance(brief, dict):
        raise ValueError("not-an-object")
except Exception as exc:  # noqa: BLE001 - malformed briefings are observations
    brief = None
    error = {"error": type(exc).__name__}
for index, probe in enumerate(probes):
    try:
        value = normalize(brief, probe) if brief is not None else error
    except Exception as exc:  # noqa: BLE001
        value = {"error": type(exc).__name__}
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
