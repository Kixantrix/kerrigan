"""Repository subset for SWE-bench Pro anchors (pure, stdlib; reads bytes, never executes them).

The agent workspace is: the hidden test files (resolved at their gold version),
their transitive LOCAL imports, the conftest.py files pytest would load for
them, the files the gold patch modifies, and the repo configuration needed to
run the tests. Python imports are resolved statically over declared source
roots; JS/TS imports (import/export-from/require/dynamic import/jest.mock)
are resolved relative to the importer, with extension and index-file probing
(including TS ``./x.js`` -> ``x.ts``) and tsconfig ``baseUrl``/``paths``.
Bare package specifiers are external (node_modules / site-packages) and skipped.
"""
from __future__ import annotations

import ast
import fnmatch
import json
import posixpath
import re

JS_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".json")
JS_SOURCE = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts")
JS_IMPORT = re.compile(
    r"""(?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s+|\brequire\s*\(\s*|\bjest\.(?:mock|requireActual|doMock)\s*\(\s*)"""
    r"""["']([^"'\n]+)["']""")
CONFIG = ("LICENSE*", "COPYING*", "package.json", "tsconfig*.json", "jest.config.*", "babel.config.*", ".babelrc", "setup.cfg",
          "pyproject.toml", "pytest.ini", "tox.ini", "setup.py", "requirements*.txt", "conftest.py")


class SubsetError(ValueError):
    pass


# ---------------------------------------------------------------- python

def python_modules(files: dict[str, bytes], roots: list[str]) -> dict[str, str]:
    """Dotted module name -> path for every .py file under the declared source roots."""
    index = {}
    for root in roots:
        prefix = f"{root.strip('/')}/" if root.strip("/") else ""
        for path in files:
            if not path.endswith(".py") or not path.startswith(prefix):
                continue
            parts = path[len(prefix):-3].split("/")
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if parts and all(p.isidentifier() for p in parts):
                index.setdefault(".".join(parts), path)
    return index


def python_imports(path: str, source: bytes, modules: dict[str, str]) -> set[str]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    package = None
    for name, target in modules.items():
        if target == path:
            package = name if path.endswith("__init__.py") else name.rpartition(".")[0]
            break
    wanted = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            wanted.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                if package is None:
                    continue
                anchor = package.split(".") if package else []
                anchor = anchor[:len(anchor) - (node.level - 1)] if node.level > 1 else anchor
                base = ".".join([*anchor, *([base] if base else [])])
            wanted.add(base)
            wanted.update(f"{base}.{alias.name}" if base else alias.name for alias in node.names)
    found = set()
    for name in wanted:
        parts = name.split(".")
        for size in range(1, len(parts) + 1):  # the module and every enclosing package __init__
            target = modules.get(".".join(parts[:size]))
            if target:
                found.add(target)
    return found


def conftests(path: str, files: dict[str, bytes]) -> set[str]:
    directory, found = posixpath.dirname(path), set()
    while True:
        candidate = posixpath.join(directory, "conftest.py") if directory else "conftest.py"
        if candidate in files:
            found.add(candidate)
        if not directory:
            return found
        directory = posixpath.dirname(directory)


# ---------------------------------------------------------------- js/ts

def strip_json_comments(text: str) -> str:
    """Drop // and /* */ comments outside JSON strings (tsconfig is JSONC)."""
    out, index, quoted = [], 0, False
    while index < len(text):
        char = text[index]
        if quoted:
            out.append(char)
            if char == "\\":
                out.append(text[index + 1:index + 2])
                index += 1
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            out.append(char)
        elif text.startswith("//", index):
            index = text.find("\n", index)
            index = len(text) if index < 0 else index
            continue
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = len(text) if end < 0 else end + 2
            continue
        else:
            out.append(char)
        index += 1
    return "".join(out)


def tsconfig_paths(files: dict[str, bytes]) -> tuple[str, dict[str, list[str]]]:
    raw = files.get("tsconfig.json")
    if raw is None:
        return "", {}
    text = re.sub(r",(\s*[}\]])", r"\1", strip_json_comments(raw.decode(errors="replace")))
    try:
        options = json.loads(text).get("compilerOptions", {})
    except ValueError:
        return "", {}
    return (options.get("baseUrl") or "").strip("./"), options.get("paths") or {}


def js_resolve(importer: str, spec: str, files: dict[str, bytes], base_url: str, aliases) -> str | None:
    spec = spec.split("?")[0].split("!")[-1]
    if spec.startswith("."):
        candidates = [posixpath.normpath(posixpath.join(posixpath.dirname(importer), spec))]
    else:
        candidates = []
        for pattern, targets in aliases.items():
            if fnmatch.fnmatchcase(spec, pattern):
                star = spec[len(pattern.split("*")[0]):len(spec) - len(pattern.split("*")[-1])] \
                    if "*" in pattern else ""
                candidates += [posixpath.normpath(posixpath.join(base_url, t.replace("*", star))) for t in targets]
        if not candidates:
            return None
    for stem in candidates:
        options = [stem, *(stem + ext for ext in JS_EXTENSIONS), *(f"{stem}/index{ext}" for ext in JS_EXTENSIONS)]
        root, ext = posixpath.splitext(stem)
        if ext in (".js", ".jsx", ".mjs", ".cjs"):
            options += [root + alt for alt in (".ts", ".tsx", ".mts", ".cts")]
        for option in options:
            if option in files:
                return option
    return None


def js_imports(path: str, source: bytes, files: dict[str, bytes], base_url: str, aliases) -> set[str]:
    text = source.decode(errors="replace")
    found = set()
    for spec in JS_IMPORT.findall(text):
        target = js_resolve(path, spec, files, base_url, aliases)
        if target:
            found.add(target)
    return found


# ---------------------------------------------------------------- closure

def resolve(files: dict[str, bytes], tests: dict[str, bytes], *, language: str, python_roots=("",),
            gold_paths=(), extra=()) -> dict:
    """Closure over local imports starting at the hidden tests (gold versions in ``tests``)."""
    view = {**files, **tests}  # gold test versions drive resolution; base bytes are exported
    modules = python_modules(view, list(python_roots)) if language == "python" else {}
    base_url, aliases = tsconfig_paths(files) if language != "python" else ("", {})
    seen, queue = set(), list(tests)
    reasons = {path: "hidden test" for path in tests}
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        source = view.get(path)
        if source is None:
            continue
        if path.endswith(".py"):
            found = python_imports(path, source, modules) | conftests(path, view)
        elif path.endswith(JS_SOURCE):
            found = js_imports(path, source, view, base_url, aliases)
        else:
            found = set()
        for target in found - seen:
            reasons.setdefault(target, f"imported by {path}")
            queue.append(target)
    for path in gold_paths:
        if path in files:
            reasons.setdefault(path, "gold patch modifies (included so the oracle diff applies)")
    for path in files:
        if "/" not in path and any(fnmatch.fnmatchcase(path, pattern) for pattern in CONFIG):
            reasons.setdefault(path, "repo configuration")
    for path in extra:
        if path in files:
            reasons.setdefault(path, "declared")
    subset = {path: reason for path, reason in reasons.items() if path in files}
    return {"paths": sorted(subset), "reasons": subset,
            "gold_only_tests": sorted(set(tests) - set(files)),
            "files": len(subset), "bytes": sum(len(files[p]) for p in subset)}
