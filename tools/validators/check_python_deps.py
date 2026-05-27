#!/usr/bin/env python3
"""Validate that Python test imports are declared in requirements.txt."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = ROOT / "requirements.txt"
ALIASES = {
    "bs4": "beautifulsoup4",
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
}
FALLBACK_STDLIB = {
    "__future__",
    "argparse",
    "ast",
    "collections",
    "contextlib",
    "datetime",
    "functools",
    "glob",
    "importlib",
    "io",
    "itertools",
    "json",
    "math",
    "os",
    "pathlib",
    "re",
    "shutil",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "typing",
    "unittest",
    "urllib",
    "uuid",
}


def normalize_requirement(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def load_requirements(requirements_path: Path) -> set[str]:
    requirements: set[str] = set()
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        package = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
        if package:
            requirements.add(normalize_requirement(package))
    return requirements


def stdlib_modules() -> set[str]:
    names = getattr(sys, "stdlib_module_names", None)
    if names:
        return set(names) | {"__future__"}
    return set(FALLBACK_STDLIB)


def first_party_modules(repo_root: Path) -> set[str]:
    modules = {
        path.name
        for path in repo_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }

    for py_file in repo_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        modules.add(py_file.stem)

    for package_init in repo_root.rglob("__init__.py"):
        modules.add(package_init.parent.name)

    return modules


def discover_test_paths(repo_root: Path) -> list[Path]:
    candidates = {path for path in repo_root.glob("tests/**/*.py") if path.is_file()}
    plan_pattern = re.compile(r"\b(tests?/[-_./*A-Za-z0-9]+)")

    for test_plan in repo_root.glob("specs/projects/*/test-plan.md"):
        text = test_plan.read_text(encoding="utf-8")
        for raw_match in plan_pattern.findall(text):
            match = raw_match.rstrip("`.,:)\"'")
            if "*" in match or "?" in match or "[" in match:
                candidates.update(path for path in repo_root.glob(match) if path.is_file())
                continue

            resolved = repo_root / match
            if resolved.is_file() and resolved.suffix == ".py":
                candidates.add(resolved)
            elif resolved.is_dir():
                candidates.update(path for path in resolved.rglob("*.py") if path.is_file())

    return sorted(candidates)


def imported_modules(test_file: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8-sig"), filename=str(test_file))
    except SyntaxError as exc:
        raise ValueError(f"failed to parse {test_file}: {exc.msg}") from exc
    imports: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name.split(".", 1)[0]))
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imports.append((node.lineno, node.module.split(".", 1)[0]))

    return imports


def find_undeclared_imports(
    repo_root: Path,
    requirements_path: Path,
) -> list[tuple[str, int, str, str]]:
    required_packages = load_requirements(requirements_path)
    stdlib = stdlib_modules()
    first_party = first_party_modules(repo_root)
    module_to_distributions = packages_distributions()
    failures: list[tuple[str, int, str, str]] = []

    for test_file in discover_test_paths(repo_root):
        relative_path = test_file.relative_to(repo_root).as_posix()
        seen: set[tuple[int, str]] = set()

        for line_no, module in imported_modules(test_file):
            key = (line_no, module)
            if key in seen or module in stdlib or module in first_party:
                continue
            seen.add(key)

            suggested = ALIASES.get(module)
            if suggested and normalize_requirement(suggested) in required_packages:
                continue

            distributions = module_to_distributions.get(module, [])
            if any(normalize_requirement(dist) in required_packages for dist in distributions):
                continue

            if not suggested:
                if distributions:
                    suggested = sorted(distributions)[0]
                else:
                    suggested = f"(unknown; check package for '{module}')"
            failures.append((relative_path, line_no, module, suggested))

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that Python test imports are declared in requirements.txt",
    )
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root to scan")
    parser.add_argument(
        "--requirements",
        default=str(REQUIREMENTS),
        help="Path to requirements.txt",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    requirements_path = Path(args.requirements).resolve()
    try:
        failures = find_undeclared_imports(repo_root, requirements_path)
    except ValueError as exc:
        print(f"check_python_deps: ERROR: {exc}", file=sys.stderr)
        return 1

    if failures:
        print("check_python_deps: FAIL", file=sys.stderr)
        print("file:line\tmodule\tsuggested-package", file=sys.stderr)
        for file_path, line_no, module, suggestion in failures:
            print(f"{file_path}:{line_no}\t{module}\t{suggestion}", file=sys.stderr)
        return 1

    print(
        f"check_python_deps: OK ({len(discover_test_paths(repo_root))} test files scanned)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
