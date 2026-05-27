# Dispatch: validator for Python dep manifest vs test imports

## Goal

Add a small static validator at `tools/validators/check_python_deps.py` that scans `tests/**/*.py` (and any project-level Python test dir referenced from `specs/projects/*/test-plan.md` if discoverable) for third-party imports and verifies each is declared in the repo's top-level `requirements.txt`.

Stdlib modules and first-party modules under repo paths are exempt. The validator must exit non-zero with a clear list of offending `(file:line, module, suggested package)` rows when there's a mismatch.

Wire it into the existing `tools/validators/__main__.py` entry point so `python -m tools.validators` runs it alongside the other validators, and add it as a step in `.github/workflows/verify.yml` (the existing `verify` job, after the unit tests step).

## Why

2026-05-27 PR #289: cloud agent added a test importing `bs4` without adding `beautifulsoup4` to `requirements.txt`. CI failed on import. The cloud-profile rule added in #299 tells the agent to verify this manually, but a static check at CI time is the belt-and-suspenders guarantee.

## Files

**Touch:**
- `tools/validators/check_python_deps.py` (new)
- `tools/validators/__main__.py` (add registration)
- `tests/test_check_python_deps.py` (new)
- `.github/workflows/verify.yml` (add step in `verify` job after existing pytest step)

**Read-only:**
- `tools/validators/check_artifacts.py` (reference for validator style + exit code conventions)
- `requirements.txt` (the manifest to check against)
- existing `tests/**/*.py` (the corpus to scan in tests)

**Out of scope:**
- Node / Rust / other languages — Python only for v1.
- Auto-fixing requirements.txt — report only.
- Editable installs / extras_require / pyproject.toml — scan `requirements.txt` only.
- Per-project requirements files under `specs/projects/<name>/` — top-level only for v1.

## Acceptance criteria

- AC-1: `python -m tools.validators.check_python_deps` exits 0 when all third-party imports in `tests/**/*.py` resolve to entries in `requirements.txt`.
- AC-2: Exits 1 with a clear table (`file:line   module   suggested-package`) when an import is undeclared.
- AC-3: Stdlib modules (use `sys.stdlib_module_names` on 3.10+; hardcode fallback list otherwise) are exempt.
- AC-4: First-party imports (top-level package name matches a directory in the repo root, e.g. `tools`, `tests`) are exempt.
- AC-5: Common name-to-package aliases handled: `bs4` → `beautifulsoup4`, `yaml` → `PyYAML`, `dotenv` → `python-dotenv`, `dateutil` → `python-dateutil`. Use a small aliases dict in the validator.
- AC-6: Registered in `tools/validators/__main__.py` so it runs from `python -m tools.validators`.
- AC-7: New job step in `.github/workflows/verify.yml` runs `python -m tools.validators.check_python_deps` and fails the workflow on non-zero exit.
- AC-8: New `tests/test_check_python_deps.py` covers: (a) clean case passes, (b) undeclared import fails with the offending module in stderr, (c) stdlib exempt, (d) alias resolution works (`bs4` declared as `beautifulsoup4` should pass).

## Test commands

```bash
pip install -r requirements.txt
python -m tools.validators.check_python_deps
pytest tests/test_check_python_deps.py -v
```

## Done-when

- All 8 ACs satisfied.
- `python -m tools.validators` exits 0 on current `main` state (no false positives on existing tests — the validator must match reality).
- New pytest test file passes.
- `.github/workflows/verify.yml` step added.

## Notes

- Keep the implementation small (<200 LOC).
- Use `ast.parse` for import extraction — don't regex.
- For the stdlib check on Python <3.10, fall back to `distutils.sysconfig` or a maintained list constant. Prefer `sys.stdlib_module_names` if `sys.version_info >= (3, 10)`.
