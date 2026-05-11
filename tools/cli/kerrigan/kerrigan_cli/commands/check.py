"""Check command - unified validator runner."""

import shutil
import subprocess
import sys
from pathlib import Path

import click


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for the repository root."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "tools" / "validators").exists():
            return parent
    return None


def _run_validator(label: str, cmd: list[str], cwd: Path, verbose: bool) -> bool:
    """Run a single validator command and return True on success."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
        )
        passed = result.returncode == 0
        status_symbol = "✓" if passed else "✗"
        click.echo(f"  {status_symbol} {label}")
        if verbose or not passed:
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    click.echo(f"      {line}")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines():
                    click.echo(f"      {line}", err=True)
        return passed
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        click.echo(f"  ✗ {label} (error: {exc})", err=True)
        return False


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Show per-validator output.")
@click.option(
    "--fast",
    is_flag=True,
    help="Skip heavy file-scanning and PR-context validators to stay under 30s.",
)
def check(verbose: bool, fast: bool) -> None:
    """Run all registered validators.

    Always runs:
      - tools/validators/agents_md.py
      - tools/validators/check_artifacts.py (if present)
      - tools/validators/check_dependencies.py (if present)
      - tools/validators/check_agent_signature.py (if present)
      - tools/validators/block_validator.py (if present)
      - tools/validators/test_capability_matrix.py (if present)
      - tools/validators/show_status.py (if present)

    Skipped with --fast (heavy / PR-context validators):
      - tools/validators/check_quality_bar.py
      - tools/validators/check_placeholders.py
      - tools/validators/check_test_collateral.py
      - tools/validators/check_pr_documentation.py
      - tools/validators/check_test_claims.py

    Also runs:
      - specify check (if specify is on PATH)

    Example:
        kerrigan check
        kerrigan check --verbose
        kerrigan check --fast
    """
    root = _find_repo_root()
    if root is None:
        click.echo("Error: Could not find Kerrigan repository root.", err=True)
        raise click.Abort()

    validators_dir = root / "tools" / "validators"
    python = sys.executable

    passed = 0
    failed = 0

    click.echo("Running validators...\n")

    # --- Always-run validators ---

    agents_md = validators_dir / "agents_md.py"
    if agents_md.exists():
        ok = _run_validator("agents_md.py", [python, str(agents_md)], root, verbose)
        if ok:
            passed += 1
        else:
            failed += 1
    else:
        click.echo(f"  ⚠ agents_md.py not found at {agents_md}", err=True)
        failed += 1

    check_artifacts = validators_dir / "check_artifacts.py"
    if check_artifacts.exists():
        ok = _run_validator(
            "check_artifacts.py", [python, str(check_artifacts)], root, verbose
        )
        if ok:
            passed += 1
        else:
            failed += 1

    check_dependencies = validators_dir / "check_dependencies.py"
    if check_dependencies.exists():
        ok = _run_validator(
            "check_dependencies.py",
            [python, str(check_dependencies)],
            root,
            verbose,
        )
        if ok:
            passed += 1
        else:
            failed += 1

    check_agent_signature = validators_dir / "check_agent_signature.py"
    if check_agent_signature.exists():
        ok = _run_validator(
            "check_agent_signature.py",
            [python, str(check_agent_signature)],
            root,
            verbose,
        )
        if ok:
            passed += 1
        else:
            failed += 1

    block_validator = validators_dir / "block_validator.py"
    if block_validator.exists():
        ok = _run_validator(
            "block_validator.py", [python, str(block_validator)], root, verbose
        )
        if ok:
            passed += 1
        else:
            failed += 1

    test_capability_matrix = validators_dir / "test_capability_matrix.py"
    if test_capability_matrix.exists():
        ok = _run_validator(
            "test_capability_matrix.py",
            [python, str(test_capability_matrix)],
            root,
            verbose,
        )
        if ok:
            passed += 1
        else:
            failed += 1

    show_status = validators_dir / "show_status.py"
    if show_status.exists():
        ok = _run_validator(
            "show_status.py", [python, str(show_status)], root, verbose
        )
        if ok:
            passed += 1
        else:
            failed += 1

    # --- Heavy / PR-context validators (skipped with --fast) ---

    if fast:
        click.echo(
            "\n  (--fast: skipping check_quality_bar, check_placeholders,"
            " check_test_collateral, check_pr_documentation, check_test_claims)"
        )
    else:
        check_quality_bar = validators_dir / "check_quality_bar.py"
        if check_quality_bar.exists():
            ok = _run_validator(
                "check_quality_bar.py",
                [python, str(check_quality_bar)],
                root,
                verbose,
            )
            if ok:
                passed += 1
            else:
                failed += 1

        check_placeholders = validators_dir / "check_placeholders.py"
        if check_placeholders.exists():
            ok = _run_validator(
                "check_placeholders.py",
                [python, str(check_placeholders)],
                root,
                verbose,
            )
            if ok:
                passed += 1
            else:
                failed += 1

        check_test_collateral = validators_dir / "check_test_collateral.py"
        if check_test_collateral.exists():
            ok = _run_validator(
                "check_test_collateral.py",
                [python, str(check_test_collateral)],
                root,
                verbose,
            )
            if ok:
                passed += 1
            else:
                failed += 1

        check_pr_documentation = validators_dir / "check_pr_documentation.py"
        if check_pr_documentation.exists():
            ok = _run_validator(
                "check_pr_documentation.py",
                [python, str(check_pr_documentation), "--repo-path", str(root)],
                root,
                verbose,
            )
            if ok:
                passed += 1
            else:
                failed += 1

        check_test_claims = validators_dir / "check_test_claims.py"
        if check_test_claims.exists():
            ok = _run_validator(
                "check_test_claims.py",
                [python, str(check_test_claims)],
                root,
                verbose,
            )
            if ok:
                passed += 1
            else:
                failed += 1

    # --- specify check (if on PATH) ---

    if shutil.which("specify"):
        ok = _run_validator("specify check", ["specify", "check"], root, verbose)
        if ok:
            passed += 1
        else:
            failed += 1
    else:
        click.echo("  - specify not found on PATH, skipping")

    # --- Summary ---

    total = passed + failed
    click.echo(f"\n{passed}/{total} validators passed, {failed}/{total} failed.")

    if failed:
        sys.exit(1)
