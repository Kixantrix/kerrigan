#!/usr/bin/env python3
"""Repo validators:
- Enforce required spec artifacts for any project folder under specs/projects/<name>/
- Enforce required sections in key docs
- Enforce autonomy gate (optional): PR label checks are not directly accessible in CI without API.
  This script enforces the *structure* that supports autonomy; the label enforcement can be added later
  via GitHub API if desired.
- Validate multi-repository project specifications (Milestone 7a)

Design philosophy: keep checks simple, actionable, and stack-agnostic.
"""

from __future__ import annotations

import json
import os
import re
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs" / "projects"

REQUIRED_FILES = [
    "spec.md",
    "acceptance-tests.md",
    "architecture.md",
    "plan.md",
    "tasks.md",
    "test-plan.md",
    # runbook.md and cost-plan.md are conditionally required; see below
]

REQUIRED_SECTIONS_SPEC = [
    "Goal",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
]

REQUIRED_SECTIONS_ARCH = [
    "Overview",
    "Components",
    "Tradeoffs",
    "Security",
]

def fail(msg: str) -> None:
    print(f"::error::{msg}")
    raise SystemExit(1)

def warn(msg: str) -> None:
    print(f"::warning::{msg}")

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"Missing required file: {p.relative_to(ROOT)}")
    except Exception as e:
        fail(f"Failed reading {p.relative_to(ROOT)}: {e}")
    return ""

def has_heading(text: str, heading: str) -> bool:
    # Match markdown headings like "# Heading" or "## Heading"
    # Don't escape spaces in the heading, only special regex chars
    # We want "Acceptance criteria" to match literally with its space
    escaped = re.escape(heading).replace('\\ ', ' ')
    pattern = re.compile(r"^#{1,6}\s+" + escaped + r"\s*$", re.MULTILINE)
    return bool(pattern.search(text))

def ensure_sections(p: Path, headings: List[str], doc_name: str) -> None:
    txt = read_text(p)
    missing = [h for h in headings if not has_heading(txt, h)]
    if missing:
        fail(f"{doc_name} missing required headings: {missing} in {p.relative_to(ROOT)}")

def project_folders() -> List[Path]:
    if not SPECS_DIR.exists():
        return []
    # Exclude test directories, special folders, and investigation/research projects
    excluded = ["_template", "_archive", "tests", "test", "test-project", "pause-resume-demo", "copilot-sdk-integration"]
    return [p for p in SPECS_DIR.iterdir() if p.is_dir() and p.name not in excluded]

def is_deployable(project_dir: Path) -> bool:
    # Heuristic: if runbook.md exists or the spec mentions "deploy" or "production"
    runbook = project_dir / "runbook.md"
    if runbook.exists():
        return True
    spec = project_dir / "spec.md"
    if spec.exists():
        txt = read_text(spec).lower()
        if "deploy" in txt or "production" in txt or "runtime" in txt:
            return True
    return False

def validate_status_json(status_path: Path, project_name: str) -> None:
    """Validate status.json structure and content."""
    try:
        content = status_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        fail(f"Project '{project_name}' has invalid JSON in status.json: {e}")
    except Exception as e:
        fail(f"Project '{project_name}' failed to read status.json: {e}")
    
    # Required fields
    required_fields = ["status", "current_phase", "last_updated"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        fail(f"Project '{project_name}' status.json missing required fields: {missing}")
    
    # Validate status values
    valid_statuses = ["active", "blocked", "completed", "on-hold"]
    if data["status"] not in valid_statuses:
        fail(f"Project '{project_name}' status.json has invalid status '{data['status']}'. Must be one of: {valid_statuses}")
    
    # Validate current_phase values
    valid_phases = ["spec", "architecture", "implementation", "testing", "deployment"]
    if data["current_phase"] not in valid_phases:
        fail(f"Project '{project_name}' status.json has invalid current_phase '{data['current_phase']}'. Must be one of: {valid_phases}")
    
    # Validate last_updated is ISO 8601 format
    try:
        datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        fail(f"Project '{project_name}' status.json has invalid last_updated timestamp. Must be ISO 8601 format: {e}")
    
    # If status is blocked, blocked_reason should be present
    if data["status"] == "blocked" and not data.get("blocked_reason"):
        warn(f"Project '{project_name}' status.json has status=blocked but no blocked_reason provided. Please add a blocked_reason field explaining why work is paused.")

def parse_yaml_frontmatter(text: str) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter from markdown file.
    
    Returns dict if frontmatter exists and is valid YAML, None otherwise.
    """
    # Match YAML frontmatter pattern: starts with ---, ends with ---
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not match:
        return None
    
    yaml_content = match.group(1)
    try:
        # Note: yaml.safe_load returns None for empty frontmatter (just --- ---),
        # which is treated the same as no frontmatter
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        # Log YAML parsing errors for debugging
        warn(f"Failed to parse YAML frontmatter: {e}")
        return None

def validate_multi_repo_spec(spec_path: Path, project_name: str) -> None:
    """Validate multi-repository project specification.
    
    Checks:
    - repositories field structure
    - repository count limit (max 5)
    - required fields (name, url, role)
    - unique repository names
    - valid GitHub URLs
    - same organization requirement
    """
    spec_text = read_text(spec_path)
    frontmatter = parse_yaml_frontmatter(spec_text)
    
    # Multi-repo is optional, so skip if no frontmatter
    if not frontmatter:
        return
    
    # If frontmatter exists but no repositories field, also ok
    if "repositories" not in frontmatter:
        return
    
    repos = frontmatter["repositories"]
    
    # Validate repositories is a list
    if not isinstance(repos, list):
        fail(f"Project '{project_name}' spec.md: 'repositories' must be a list")
    
    # Check repository count limit
    if len(repos) > 5:
        fail(f"Project '{project_name}' spec.md: Maximum 5 repositories allowed, found {len(repos)}")
    
    if len(repos) == 0:
        warn(f"Project '{project_name}' spec.md: 'repositories' array is empty. Remove it if not using multi-repo.")
        return
    
    # Track repository names for uniqueness check
    repo_names = set()
    repo_orgs = set()
    
    for idx, repo in enumerate(repos):
        if not isinstance(repo, dict):
            fail(f"Project '{project_name}' spec.md: Repository at index {idx} must be an object")
        
        # Check required fields
        required_fields = ["name", "url", "role"]
        missing = [f for f in required_fields if f not in repo]
        if missing:
            fail(f"Project '{project_name}' spec.md: Repository at index {idx} missing required fields: {missing}")
        
        name = repo["name"]
        url = repo["url"]
        role = repo["role"]
        
        # Validate that name and url are strings before using them in string operations
        if not isinstance(name, str):
            fail(f"Project '{project_name}' spec.md: Repository name at index {idx} must be a string")
        
        if not isinstance(url, str):
            fail(f"Project '{project_name}' spec.md: Repository URL at index {idx} must be a string")
        
        # Validate name format (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            fail(f"Project '{project_name}' spec.md: Repository name '{name}' must contain only alphanumeric characters, hyphens, and underscores")
        
        # Check for duplicate names
        if name in repo_names:
            fail(f"Project '{project_name}' spec.md: Duplicate repository name '{name}'")
        repo_names.add(name)
        
        # Validate URL format (must be GitHub HTTPS URL)
        github_pattern = r'^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.match(github_pattern, url)
        if not match:
            fail(f"Project '{project_name}' spec.md: Repository '{name}' has invalid GitHub URL: {url}")
        
        # Extract organization from URL
        org = match.group(1)
        repo_orgs.add(org)
        
        # Validate role is non-empty string
        if not isinstance(role, str) or not role.strip():
            fail(f"Project '{project_name}' spec.md: Repository '{name}' role must be a non-empty string")
    
    # Check same organization requirement
    if len(repo_orgs) > 1:
        fail(f"Project '{project_name}' spec.md: All repositories must be in the same GitHub organization. Found: {sorted(repo_orgs)}")

def validate_cross_repo_references(project_dir: Path, project_name: str) -> None:
    """Validate cross-repository references in project artifacts.
    
    Checks that repo:path references use valid repository names from the repositories array.
    This is a basic syntax check; full validation (checking if files exist) is future work.
    """
    spec_path = project_dir / "spec.md"
    spec_text = read_text(spec_path)
    frontmatter = parse_yaml_frontmatter(spec_text)
    
    # Skip if not a multi-repo project
    if not frontmatter or "repositories" not in frontmatter:
        return
    
    repos = frontmatter.get("repositories", [])
    if not repos:
        return
    
    # Build set of valid repository names.
    # Note: validate_multi_repo_spec is expected to enforce repository structure,
    # but this logic is intentionally defensive in case malformed entries appear here.
    valid_repo_names = set()
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        name = repo.get("name")
        if isinstance(name, str) and name:
            valid_repo_names.add(name)
    
    # Pattern to match repo:path references
    # Matches: reponame:path/to/file.md or (see reponame:path) or [text](reponame:path)
    # Path component allows alphanumeric, underscore, forward slash, dot, hash, and hyphen
    # Hash (#) is included to support fragment identifiers (e.g., api:spec.md#versioning)
    ref_pattern = r'\b([a-zA-Z0-9_-]+):([a-zA-Z0-9_/.#-]+)'
    
    # Check all markdown files in the project
    for md_file in project_dir.glob("*.md"):
        content = read_text(md_file)
        
        # Find all cross-repo references
        for match in re.finditer(ref_pattern, content):
            repo_name = match.group(1)
            path = match.group(2)
            
            # Check if the repository name is valid
            # Only warn for now since this could have false positives (e.g., URLs with colons)
            if repo_name not in valid_repo_names:
                # Only warn if it looks like it could be a cross-repo reference
                # (not a URL scheme like http:, https:, etc.)
                common_schemes = ["http", "https", "ftp", "ssh", "git", "file", "mailto"]
                if repo_name.lower() not in common_schemes:
                    warn(f"Project '{project_name}' {md_file.name}: Found reference '{repo_name}:{path}' but '{repo_name}' is not in repositories array. If this is a cross-repo reference, add '{repo_name}' to repositories.")


def main() -> None:
    # Constitution must exist
    constitution = ROOT / "specs" / "constitution.md"
    if not constitution.exists():
        fail("Missing specs/constitution.md (governing principles).")

    # Validate each project folder
    for proj in project_folders():
        for f in REQUIRED_FILES:
            path = proj / f
            if not path.exists():
                fail(f"Project '{proj.name}' missing required file {f} at {path.relative_to(ROOT)}")

        # Required sections
        ensure_sections(proj / "spec.md", REQUIRED_SECTIONS_SPEC, "spec.md")
        # Architecture headings are matched loosely via keywords
        arch_txt = read_text(proj / "architecture.md")
        # Require presence of these section headings (exact names from template)
        ensure_sections(proj / "architecture.md", ["Overview", "Components & interfaces", "Tradeoffs", "Security & privacy notes"], "architecture.md")

        # Conditional runbook/cost plan
        if is_deployable(proj):
            for f in ["runbook.md", "cost-plan.md"]:
                if not (proj / f).exists():
                    fail(f"Project '{proj.name}' appears deployable but is missing {f}.")
        
        # Optional status.json validation
        status_json = proj / "status.json"
        if status_json.exists():
            validate_status_json(status_json, proj.name)
        
        # Multi-repository validation (Milestone 7a)
        spec_md = proj / "spec.md"
        validate_multi_repo_spec(spec_md, proj.name)
        validate_cross_repo_references(proj, proj.name)
    
    print("Artifact checks passed.")

if __name__ == "__main__":
    main()
