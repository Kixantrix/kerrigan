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
OPTIONAL_TEST_DEPS_ALLOWLIST = ROOT / ".github" / "optional-test-deps.txt"
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


def load_optional_test_dependencies(allowlist_path: Path) -> set[str]:
    if not allowlist_path.exists():
        return set()

    optional_dependencies: set[str] = set()
    for raw_line in allowlist_path.read_text(encoding="utf-8").splitlines():
        module = raw_line.split("#", 1)[0].strip()
        if module:
            optional_dependencies.add(module.split(".", 1)[0])
    return optional_dependencies


def first_party_modules(repo_root: Path) -> set[str]:
    modules: set[str] = set()
    for path in repo_root.iterdir():
        if path.name.startswith("."):
            continue
        if path.is_dir() and (path / "__init__.py").is_file():
            modules.add(path.name)
        elif path.is_file() and path.suffix == ".py" and path.name != "__init__.py":
            modules.add(path.stem)
    return modules


def _path_from_expr(node: ast.AST, *, file_path: Path, env: dict[str, Path]) -> Path | None:
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return file_path
        return env.get(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return Path(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _path_from_expr(node.left, file_path=file_path, env=env)
        right = _path_from_expr(node.right, file_path=file_path, env=env)
        if left is not None and right is not None:
            return left / str(right)
        return None
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id == "Path" and len(node.args) == 1:
                arg = _path_from_expr(node.args[0], file_path=file_path, env=env)
                if arg is not None:
                    return Path(arg)
            if node.func.id == "str" and len(node.args) == 1:
                return _path_from_expr(node.args[0], file_path=file_path, env=env)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "dirname"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "path"
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
            and len(node.args) == 1
        ):
            arg = _path_from_expr(node.args[0], file_path=file_path, env=env)
            if arg is not None:
                return Path(arg).parent
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "path"
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "os"
            and node.args
        ):
            parts: list[Path | str] = []
            for arg in node.args:
                resolved = _path_from_expr(arg, file_path=file_path, env=env)
                if resolved is not None:
                    parts.append(resolved)
                    continue
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    parts.append(arg.value)
                    continue
                return None
            current = Path(parts[0])
            for part in parts[1:]:
                current = current / str(part)
            return current
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "resolve"
            and not node.args
            and not node.keywords
        ):
            base = _path_from_expr(node.func.value, file_path=file_path, env=env)
            if base is not None:
                return base.resolve()
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        base = _path_from_expr(node.value, file_path=file_path, env=env)
        if base is not None:
            return base.parent
    if isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
            base = _path_from_expr(node.value.value, file_path=file_path, env=env)
            index_node = node.slice
            if isinstance(index_node, ast.Constant) and isinstance(index_node.value, int):
                index = index_node.value
            else:
                return None
            if base is not None and index >= 0:
                try:
                    return base.parents[index]
                except IndexError:
                    return None
    return None


def _is_sys_path_insert(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute) or func.attr != "insert":
        return False
    path_attr = func.value
    return (
        isinstance(path_attr, ast.Attribute)
        and path_attr.attr == "path"
        and isinstance(path_attr.value, ast.Name)
        and path_attr.value.id == "sys"
    )


def test_import_roots(test_file: Path, repo_root: Path) -> list[Path]:
    source = test_file.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(test_file))
    env: dict[str, Path] = {}
    import_roots: list[Path] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                resolved = _path_from_expr(node.value, file_path=test_file, env=env)
                if resolved is not None:
                    env[target.id] = resolved
        elif isinstance(node, ast.Call) and _is_sys_path_insert(node) and len(node.args) >= 2:
            resolved = _path_from_expr(node.args[1], file_path=test_file, env=env)
            if resolved is None:
                continue
            try:
                normalized = resolved.resolve()
            except OSError:
                continue
            try:
                normalized.relative_to(repo_root)
            except ValueError:
                continue
            if normalized.is_dir():
                import_roots.append(normalized)

    return import_roots


def modules_in_import_root(import_root: Path) -> set[str]:
    modules: set[str] = set()
    for path in import_root.iterdir():
        if path.name.startswith("."):
            continue
        if path.is_file() and path.suffix == ".py" and path.name != "__init__.py":
            modules.add(path.stem)
        elif path.is_dir() and (path / "__init__.py").is_file():
            modules.add(path.name)
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
    optional_test_deps_allowlist_path: Path,
) -> list[tuple[str, int, str, str]]:
    required_packages = load_requirements(requirements_path)
    stdlib = stdlib_modules()
    first_party = first_party_modules(repo_root)
    optional_test_deps = load_optional_test_dependencies(optional_test_deps_allowlist_path)
    module_to_distributions = packages_distributions()
    failures: list[tuple[str, int, str, str]] = []

    for test_file in discover_test_paths(repo_root):
        relative_path = test_file.relative_to(repo_root).as_posix()
        seen: set[tuple[int, str]] = set()
        first_party_for_test = set(first_party)
        for import_root in test_import_roots(test_file, repo_root):
            first_party_for_test.update(modules_in_import_root(import_root))

        for line_no, module in imported_modules(test_file):
            key = (line_no, module)
            if (
                key in seen
                or module in stdlib
                or module in first_party_for_test
                or module in optional_test_deps
            ):
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
    parser.add_argument(
        "--optional-test-deps-allowlist",
        default=str(OPTIONAL_TEST_DEPS_ALLOWLIST),
        help="Path to optional test dependency allowlist",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    requirements_path = Path(args.requirements).resolve()
    optional_test_deps_allowlist_path = Path(args.optional_test_deps_allowlist).resolve()
    try:
        failures = find_undeclared_imports(
            repo_root,
            requirements_path,
            optional_test_deps_allowlist_path,
        )
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
