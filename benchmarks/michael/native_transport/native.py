"""Session-owned requested configuration only; native execution remains fail-closed."""
import hashlib
import json
from pathlib import Path
import sys

from broker import REQUIREMENT, TOOL

MODELS = ("mai-code-2", "claude-sonnet-5.5")


def fixture(directory, model, run_id, evidence, deadline):
    if model not in MODELS:
        raise ValueError("unapproved model; no fallback")
    directory = Path(directory).resolve()
    if any((parent / ".git").exists() for parent in (directory, *directory.parents)):
        raise ValueError("fixture must be outside repository/history")
    directory.mkdir(parents=True, exist_ok=False)
    agents = directory / ".github" / "agents"
    agents.mkdir(parents=True)
    profile = agents / "mb-canary.agent.md"
    profile.write_text(
        f"---\nname: mb-canary\ndescription: Synthetic broker canary\nmodel: {model}\n"
        'model-policy: required\ntools: ["mb-broker/action"]\nstrict-tools-list: true\n---\n'
        + REQUIREMENT)
    config = directory / "mcp.json"
    config.write_text(json.dumps({"mcpServers": {"mb-broker": {
        "type": "stdio", "command": sys.executable,
        "args": [str(Path(__file__).with_name("broker.py")), run_id, str(evidence), str(deadline)],
        "tools": ["action"], "disableToolCache": True,
        "env": {"PATH": "/usr/local/bin:/usr/bin:/bin"}}}}, indent=2))
    argv = ["copilot", "--no-auto-update", "--model", model, "--agent", "mb-canary",
            "--available-tools", TOOL, "--allow-tool=mb-broker(action)",
            "--disable-builtin-mcps", "--no-ask-user", "--disallow-temp-dir",
            "--secret-env-vars=COPILOT_GITHUB_TOKEN,GH_TOKEN,GITHUB_TOKEN",
            "--sync-session=off", "--log-level=none", "--trust-folder",
            "--additional-mcp-config", f"@{config}", "--output-format=json"]
    return {"requested_model": model, "observed_model": "unknown", "argv": argv,
            "cwd": str(directory), "environment_overrides": {
                "COPILOT_HOME": str(directory / "state"),
                "COPILOT_CACHE_HOME": str(directory / "cache"),
                "COPILOT_PLUGIN_DIR_ONLY": "true", "COPILOT_MCP_TOOL_CACHE": "false",
                "COPILOT_DISABLE_LOGIN_SHELL_ENV": "true",
                "COPILOT_CUSTOM_INSTRUCTIONS_DIRS": "", "COPILOT_ALLOW_ALL": "false"},
            "effective_inventory": "unknown", "native_launch": "blocked",
            "hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in (profile, config)}}
