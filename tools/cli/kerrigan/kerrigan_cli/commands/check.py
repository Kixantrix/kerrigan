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
def check(verbose: bool) -> None:
    """Run all validators and optionally specify check.

    Runs:
      - tools/validators/agents_md.py
      - tools/validators/check_artifacts.py (if present)
      - specify check (if specify is on PATH)

    Example:
        kerrigan check
        kerrigan check --verbose
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

    # AC-2: always run agents_md.py
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

    # AC-3: run check_artifacts.py if present
    check_artifacts = validators_dir / "check_artifacts.py"
    if check_artifacts.exists():
        ok = _run_validator(
            "check_artifacts.py", [python, str(check_artifacts)], root, verbose
        )
        if ok:
            passed += 1
        else:
            failed += 1

    # AC-4: run specify check if on PATH
    if shutil.which("specify"):
        ok = _run_validator("specify check", ["specify", "check"], root, verbose)
        if ok:
            passed += 1
        else:
            failed += 1
    else:
        click.echo("  - specify not found on PATH, skipping")

    # AC-5: summary
    total = passed + failed
    click.echo(f"\n{passed}/{total} validators passed, {failed}/{total} failed.")

    if failed:
        sys.exit(1)
