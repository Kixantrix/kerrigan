"""Check command - unified validator runner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import click


@dataclass(frozen=True)
class ValidatorSpec:
    """Validator registration for ``kerrigan check``."""

    script_name: str
    label: str
    blocking: bool = True


@dataclass(frozen=True)
class CheckContext:
    """Runtime context shared across validator invocations."""

    python: str
    root: Path
    pr_body_file: Path | None
    test_claims_base_ref: str
    test_claims_head_ref: str = "HEAD"


REGISTERED_VALIDATORS: tuple[ValidatorSpec, ...] = (
    ValidatorSpec("show_status.py", "show_status.py"),
    ValidatorSpec("agents_md.py", "agents_md.py"),
    ValidatorSpec("block_validator.py", "block_validator.py"),
    ValidatorSpec("check_agent_signature.py", "check_agent_signature.py"),
    ValidatorSpec("check_artifacts.py", "check_artifacts.py"),
    ValidatorSpec("check_dependencies.py", "check_dependencies.py"),
    ValidatorSpec("check_placeholders.py", "check_placeholders.py"),
    ValidatorSpec("check_pr_documentation.py", "check_pr_documentation.py", blocking=False),
    ValidatorSpec("check_quality_bar.py", "check_quality_bar.py"),
    ValidatorSpec("check_test_claims.py", "check_test_claims.py"),
    ValidatorSpec("check_test_collateral.py", "check_test_collateral.py", blocking=False),
    ValidatorSpec("test_capability_matrix.py", "test_capability_matrix.py"),
)


def _find_repo_root() -> Path | None:
    """Walk up from cwd looking for the repository root."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "tools" / "validators").exists():
            return parent
    return None


def _load_pr_body_file() -> Path | None:
    """Materialize the PR body from the GitHub event payload when available."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None

    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        return None

    pr_body = pull_request.get("body")
    if not isinstance(pr_body, str):
        return None

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="kerrigan-pr-body-",
        suffix=".md",
        delete=False,
    ) as handle:
        handle.write(pr_body)
        return Path(handle.name)


def _build_check_context(root: Path) -> CheckContext:
    """Build the runtime context for validator execution."""
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        base_ref = f"origin/{base_ref}"
    else:
        base_ref = "main"

    return CheckContext(
        python=sys.executable,
        root=root,
        pr_body_file=_load_pr_body_file(),
        test_claims_base_ref=base_ref,
    )


def _validator_cmd(spec: ValidatorSpec, context: CheckContext) -> list[str]:
    """Return the subprocess command for a registered validator."""
    validator_path = context.root / "tools" / "validators" / spec.script_name

    if spec.script_name == "check_pr_documentation.py":
        cmd = [context.python, str(validator_path), "--repo-path", str(context.root)]
        if context.pr_body_file is not None:
            cmd.extend(["--pr-body", str(context.pr_body_file)])
        return cmd

    if spec.script_name == "check_test_claims.py":
        cmd = [
            context.python,
            str(validator_path),
            "--base-ref",
            context.test_claims_base_ref,
            "--head-ref",
            context.test_claims_head_ref,
        ]
        if context.pr_body_file is not None:
            cmd.extend(["--pr-body", str(context.pr_body_file)])
        return cmd

    return [context.python, str(validator_path)]


def _run_validator(
    label: str,
    cmd: list[str],
    cwd: Path,
    verbose: bool,
    *,
    blocking: bool,
) -> str:
    """Run a single validator command and return its outcome."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        click.echo(f"  ✗ {label} (error: {exc})", err=True)
        return "failed"

    if result.returncode == 0:
        status = "passed"
        status_symbol = "✓"
    elif blocking:
        status = "failed"
        status_symbol = "✗"
    else:
        status = "advisory"
        status_symbol = "!"

    click.echo(f"  {status_symbol} {label}")

    if verbose or result.returncode != 0:
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                click.echo(f"      {line}")
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines():
                click.echo(f"      {line}", err=True)

    if status == "advisory":
        click.echo("      advisory validator returned non-zero; continuing")

    return status


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Show per-validator output.")
def check(verbose: bool) -> None:
    """Run all registered validators and optionally specify check.

    Example:
        kerrigan check
        kerrigan check --verbose
    """
    root = _find_repo_root()
    if root is None:
        click.echo("Error: Could not find Kerrigan repository root.", err=True)
        raise click.Abort()

    validators_dir = root / "tools" / "validators"
    context = _build_check_context(root)

    passed = 0
    failed = 0
    advisory = 0

    click.echo("Running validators...\n")

    registered = {spec.script_name: spec for spec in REGISTERED_VALIDATORS}
    present_validators = sorted(path.name for path in validators_dir.glob("*.py"))

    for script_name in sorted(set(present_validators) - set(registered)):
        click.echo(f"  ✗ {script_name} is not registered in kerrigan check", err=True)
        failed += 1

    for spec in REGISTERED_VALIDATORS:
        if spec.script_name not in present_validators:
            continue

        result = _run_validator(
            spec.label,
            _validator_cmd(spec, context),
            root,
            verbose,
            blocking=spec.blocking,
        )

        if result == "passed":
            passed += 1
        elif result == "advisory":
            advisory += 1
        else:
            failed += 1

    if shutil.which("specify"):
        result = _run_validator(
            "specify check",
            ["specify", "check"],
            root,
            verbose,
            blocking=True,
        )
        if result == "passed":
            passed += 1
        else:
            failed += 1
    else:
        click.echo("  - specify not found on PATH, skipping")

    total = passed + failed + advisory
    click.echo(
        f"\n{passed}/{total} validators passed, "
        f"{advisory}/{total} advisory, {failed}/{total} failed."
    )

    if context.pr_body_file is not None:
        context.pr_body_file.unlink(missing_ok=True)

    if failed:
        sys.exit(1)
