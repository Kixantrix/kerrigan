"""Answer-free sandbox adapter. All its output is untrusted observation data."""

import importlib.util
import json
from pathlib import Path

app = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("agents_md", app / "tools/validators/agents_md.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
probes = json.loads((app / "probes.json").read_text())
for index, probe in enumerate(probes):
    root = Path("/work") / str(index)
    root.mkdir()
    candidate.REPO_ROOT = root
    candidate.AGENTS_MD = root / "AGENTS.md"
    if probe["op"] == "parse":
        value = candidate.parse_frontmatter(probe["text"])
    else:
        path = root / probe["path"]
        if probe["text"] is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(probe["text"], encoding="utf-8")
        value = []
        if probe["op"] == "agents":
            candidate.check_agents_md(value)
        else:
            function = candidate.check_agent_profile if probe["op"] == "profile" else candidate.check_skill
            function(path, value)
    print(json.dumps({"id": index, "value": value}, allow_nan=False), flush=True)
