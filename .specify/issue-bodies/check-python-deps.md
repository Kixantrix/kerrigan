## Briefing

Full briefing: [.specify/briefings/check-python-deps.md](.specify/briefings/check-python-deps.md) (lands with #299; if you can't see it on `main` yet, wait for #299 to merge or read from the `chore/dispatch-fixes` branch).

## TL;DR

Add `tools/validators/check_python_deps.py` to fail CI when a Python test imports a third-party package that's not in `requirements.txt`. Belt-and-suspenders for the cloud-profile rule landed in #299. Cautionary case: 2026-05-27 PR #289 pushed a test importing `bs4` without adding `beautifulsoup4` to `requirements.txt`.

## Acceptance criteria

See briefing AC-1 through AC-8.

## Files in scope

- `tools/validators/check_python_deps.py` (new)
- `tools/validators/__main__.py` (register)
- `tests/test_check_python_deps.py` (new)
- `.github/workflows/verify.yml` (add step)

## Done-when

All 8 ACs satisfied, briefing's test commands all green, no false positives on current `tests/` corpus.
