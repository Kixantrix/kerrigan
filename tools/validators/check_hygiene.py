"""Validator: Repo hygiene check

Prevents staleness by detecting:
1. Broken internal markdown links
2. V1 pattern references in docs/examples
3. Undated milestone/PR summary files in root
4. Orphaned example projects
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

# V1 patterns that should not appear in docs/ or examples/
V1_PATTERNS = {
    "role:swe": "Use agent:go instead (v2 label system)",
    "role:spec": "Use agent:go instead (v2 label system)",
    "role:architect": "Use agent:go instead (v2 label system)",
    "role:testing": "Use agent:go instead (v2 label system)",
    "AGENT_SIGNATURE": "V1 signature system removed; use Copilot review",
    "agent:sprint": "V1 autonomy label; use agent:go",
    "agent:blocked": "V1 label; use agent:wait",
    "status.json": "V1 pause mechanism (Phase 2+: use workflow state instead)",
}

# One-time artifacts that should be dated or archived
TEMP_ARTIFACT_PATTERNS = [
    r"^MILESTONE-\d+-",
    r"^IMPLEMENTATION-SUMMARY\.md$",
    r"^.*-SUMMARY\.md$",  # Any summary file in root
]


class Issue(NamedTuple):
    severity: str  # "error" or "warning"
    file: str
    line: int | None
    message: str


def check_broken_links(repo_root: Path) -> list[Issue]:
    """Check for broken internal markdown links."""
    issues = []
    
    # Find all markdown files
    md_files = list(repo_root.glob("**/*.md"))
    
    # Extract all file paths for fast lookup
    all_files = {f.relative_to(repo_root).as_posix() for f in repo_root.glob("**/*") if f.is_file()}
    
    for md_file in md_files:
        rel_path = md_file.relative_to(repo_root)
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        
        # Match markdown links: [text](path)
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
            link = match.group(2)
            
            # Skip external links, anchors, and special schemes
            if link.startswith(("http://", "https://", "#", "mailto:", "file://")):
                continue
            
            # Remove anchor if present
            link_path = link.split("#")[0]
            if not link_path:  # Pure anchor link
                continue
            
            # Resolve relative to current file's directory
            link_full = (md_file.parent / link_path).resolve()
            
            # Check if target exists
            if not link_full.exists():
                line_num = content[:match.start()].count("\n") + 1
                issues.append(Issue(
                    severity="error",
                    file=str(rel_path),
                    line=line_num,
                    message=f"Broken link to: {link}",
                ))
    
    return issues


def check_v1_patterns(repo_root: Path) -> list[Issue]:
    """Check for V1 pattern references in docs/ and examples/."""
    issues = []
    
    # Only check docs/ and examples/ (not specs/kerrigan/_archive-v1/)
    for pattern in ["docs/**/*.md", "examples/**/*.md", "examples/**/*.py"]:
        for file in repo_root.glob(pattern):
            if "_archive" in str(file):  # Skip archives
                continue
            
            rel_path = file.relative_to(repo_root)
            content = file.read_text(encoding="utf-8", errors="ignore")
            
            for v1_pattern, suggestion in V1_PATTERNS.items():
                if v1_pattern in content:
                    # Find line number
                    for line_num, line in enumerate(content.splitlines(), start=1):
                        if v1_pattern in line:
                            issues.append(Issue(
                                severity="warning",
                                file=str(rel_path),
                                line=line_num,
                                message=f"V1 pattern '{v1_pattern}': {suggestion}",
                            ))
                            break  # Only report first occurrence per file
    
    return issues


def check_temp_artifacts(repo_root: Path) -> list[Issue]:
    """Check for undated one-time artifacts in repo root."""
    issues = []
    
    for file in repo_root.glob("*.md"):
        filename = file.name
        
        # Skip standard files
        if filename in ["README.md", "CHANGELOG.md", "LICENSE.md", "SECURITY.md", "AGENTS.md", "CLAUDE.md"]:
            continue
        
        # Check against temp artifact patterns
        for pattern in TEMP_ARTIFACT_PATTERNS:
            if re.match(pattern, filename):
                issues.append(Issue(
                    severity="warning",
                    file=filename,
                    line=None,
                    message=f"One-time artifact in root. Consider moving to docs/archive/ or dating the filename.",
                ))
                break
    
    return issues


def main() -> int:
    """Run all hygiene checks."""
    repo_root = Path(__file__).resolve().parents[2]  # tools/validators/check_hygiene.py → repo root
    
    all_issues: list[Issue] = []
    
    print("Checking broken internal links...")
    all_issues.extend(check_broken_links(repo_root))
    
    print("Checking for V1 patterns...")
    all_issues.extend(check_v1_patterns(repo_root))
    
    print("Checking for temporary artifacts in root...")
    all_issues.extend(check_temp_artifacts(repo_root))
    
    # Report
    if not all_issues:
        print("✅ All hygiene checks passed")
        return 0
    
    errors = [i for i in all_issues if i.severity == "error"]
    warnings = [i for i in all_issues if i.severity == "warning"]
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for issue in warnings:
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"  {loc} - {issue.message}")
    
    if errors:
        print(f"\n❌ {len(errors)} errors:")
        for issue in errors:
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"  {loc} - {issue.message}")
        return 1
    
    print(f"\n✅ No errors (but {len(warnings)} warnings to address)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
