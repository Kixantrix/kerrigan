"""Standalone agent-validator bootstrap contract and subprocess coverage."""

import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import venv

import pytest
import yaml


ROOT = Path(__file__).resolve().parent.parent


def test_bootstrap_copies_dependency_manifest_before_install_and_validation():
    text = (ROOT / "playbooks" / "v2-bootstrap.md").read_text(encoding="utf-8")
    paths = re.search(r"\$layerPaths = @\((.*?)\n\)", text, re.DOTALL)
    assert paths is not None
    entries = re.findall(r"'([^']+)'", paths.group(1))
    assert "tools/validators/agents_md.py" in entries
    assert "tools/validators/requirements.txt" in entries
    for entry in entries:
        assert ROOT.joinpath(*entry.split("/")).exists()
    assert "$destination = Join-Path (Get-Location) $relativePath" in text
    install = "python -m pip install -r tools/validators/requirements.txt"
    validate = "python tools/validators/agents_md.py"
    new_repo, migration = text.split("## Migrate a v1 satellite", 1)
    for section in (new_repo, migration):
        assert section.index(install) < section.index(validate)
        assert "if ($LASTEXITCODE -ne 0)" in section
    standalone = (ROOT / "tools" / "validators" / "requirements.txt").read_text().strip()
    assert standalone == "PyYAML==6.0.2"
    assert standalone in (ROOT / "requirements.txt").read_text().splitlines()


def test_standalone_validator_requires_declared_dependency_then_validates(tmp_path):
    validator = tmp_path / "tools" / "validators" / "agents_md.py"
    validator.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "tools" / "validators" / "agents_md.py", validator)
    shutil.copy2(
        ROOT / "tools" / "validators" / "requirements.txt",
        validator.parent / "requirements.txt",
    )
    shutil.copy2(ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    profiles = tmp_path / ".github" / "agents"
    profiles.mkdir(parents=True)
    for name in ("cloud", "kerrigan"):
        shutil.copy2(ROOT / ".github" / "agents" / f"{name}.md", profiles)
    env = {**os.environ, "PYTHONPATH": "", "PYTHONUTF8": "1"}

    def run():
        return subprocess.run(
            [sys.executable, "-S", str(validator)],
            cwd=tmp_path, env=env, capture_output=True, text=True, check=False,
        )

    missing = run()
    assert missing.returncode == 1
    assert "PyYAML is required" in missing.stderr
    assert "pip install -r tools/validators/requirements.txt" in missing.stderr
    assert "validator: OK" not in missing.stdout

    # Supply only the already-installed declared dependency, without site-packages.
    dependencies = tmp_path / "dependencies"
    shutil.copytree(Path(yaml.__file__).parent, dependencies / "yaml")
    env["PYTHONPATH"] = str(dependencies)
    valid = run()
    assert valid.returncode == 0, valid.stdout + valid.stderr
    assert "OK (2 profiles)" in valid.stdout
    cloud = profiles / "cloud.md"
    cloud.write_text(
        cloud.read_text(encoding="utf-8").replace("mcp-servers: {}", "mcp-servers: []"),
        encoding="utf-8",
    )
    invalid = run()
    assert invalid.returncode == 1
    assert "'mcp-servers' must be a mapping" in invalid.stdout


@pytest.mark.parametrize("mode", ["validate-only", "install-fails", "install-without-module"])
def test_shell_bootstrap_missing_dependency_is_not_silent(tmp_path, mode):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash bootstrap requires Bash (Git Bash on Windows)")
    tools = tmp_path / "tools"
    tools.mkdir()
    shutil.copy2(ROOT / "tools" / "bootstrap.sh", tools / "bootstrap.sh")
    (tools / "validators").mkdir()
    shutil.copy2(
        ROOT / "tools" / "validators" / "requirements.txt",
        tools / "validators" / "requirements.txt",
    )
    python_only = tmp_path / "python-only"
    venv.EnvBuilder(with_pip=False).create(python_only)
    executable = (
        python_only / "Scripts" / "python.exe"
        if os.name == "nt" else python_only / "bin" / "python"
    )
    # Refuse pip network operations while recording the install attempt.
    command = f"""
python3() {{
    if [ "$1" = "-m" ] && [ "$2" = "pip" ]; then
        echo "INSTALL_ATTEMPT:$*"
        return {0 if mode == "install-without-module" else 23}
    fi
    {shlex.quote(str(executable))} "$@"
}}
export -f python3
bash tools/bootstrap.sh --skip-github {"--validate-only" if mode == "validate-only" else ""}
"""
    result = subprocess.run(
        [bash], input=command, cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": "", "PYTHONUTF8": "1"},
        capture_output=True, text=True, check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "Step 2:" not in output
    assert "All checks passed" not in output
    if mode == "validate-only":
        assert "PyYAML is required. Install with:" in output
        assert "INSTALL_ATTEMPT:" not in output
    else:
        assert "INSTALL_ATTEMPT:-m pip install -r tools/validators/requirements.txt" in output
        message = (
            "PyYAML is still unavailable after installation"
            if mode == "install-without-module" else "Validator dependency installation failed"
        )
        assert message in output
