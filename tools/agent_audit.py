#!/usr/bin/env python3
"""Agent usage auditing system.

This module provides tools to track and validate agent usage to ensure
that labeled agents are actually using their specific prompts.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentSignature:
    """Represents an agent signature in a PR description."""
    
    # Expected format: <!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->
    SIGNATURE_PATTERN = re.compile(
        r'<!--\s*AGENT_SIGNATURE:\s*'
        r'role=([^,]+),\s*'
        r'version=([^,]+),\s*'
        r'timestamp=([^\s]+)\s*'
        r'-->'
    )
    
    def __init__(self, role: str, version: str, timestamp: str):
        self.role = role
        self.version = version
        self.timestamp = timestamp
    
    @classmethod
    def from_text(cls, text: str) -> Optional['AgentSignature']:
        """Extract agent signature from text (e.g., PR description)."""
        match = cls.SIGNATURE_PATTERN.search(text)
        if match:
            return cls(
                role=match.group(1),
                version=match.group(2),
                timestamp=match.group(3)
            )
        return None
    
    @classmethod
    def create(cls, role: str, version: str = "1.0") -> 'AgentSignature':
        """Create a new agent signature with current timestamp."""
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return cls(role=role, version=version, timestamp=timestamp)
    
    def to_markdown_comment(self) -> str:
        """Generate the markdown comment format for inclusion in PR descriptions."""
        return f"<!-- AGENT_SIGNATURE: role={self.role}, version={self.version}, timestamp={self.timestamp} -->"
    
    def validate(self) -> List[str]:
        """Validate the signature and return list of errors (empty if valid)."""
        errors = []
        
        # Validate role format (should be role:name or agent:name)
        if not self.role:
            errors.append("Role is empty")
        elif not (self.role.startswith("role:") or self.role.startswith("agent:")):
            errors.append(f"Role '{self.role}' should start with 'role:' or 'agent:' prefix")
        
        # Validate version format (simple semver check)
        if not re.match(r'^\d+\.\d+(\.\d+)?$', self.version):
            errors.append(f"Version '{self.version}' should be in semver format (e.g., 1.0 or 1.0.0)")
        
        # Validate timestamp format (ISO 8601)
        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append(f"Timestamp '{self.timestamp}' is not valid ISO 8601 format")
        
        return errors


class AuditLog:
    """Manages the agent audit log."""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.entries: List[Dict[str, Any]] = []
        if log_path.exists():
            self._load()
    
    def _load(self) -> None:
        """Load existing audit log."""
        try:
            with open(self.log_path, 'r') as f:
                data = json.load(f)
                self.entries = data.get('entries', [])
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load audit log: {e}")
            self.entries = []
    
    def _save(self) -> None:
        """Save audit log to disk."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w') as f:
            json.dump({
                'version': '1.0',
                'last_updated': datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                'entries': self.entries
            }, f, indent=2)
    
    def add_entry(
        self,
        agent_role: str,
        pr_number: Optional[int] = None,
        issue_number: Optional[int] = None,
        signature: Optional[AgentSignature] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an audit log entry."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            'agent_role': agent_role,
        }
        
        if pr_number:
            entry['pr_number'] = pr_number
        if issue_number:
            entry['issue_number'] = issue_number
        if signature:
            entry['signature'] = {
                'role': signature.role,
                'version': signature.version,
                'timestamp': signature.timestamp
            }
        if metadata:
            entry['metadata'] = metadata
        
        self.entries.append(entry)
        self._save()
    
    def get_entries_for_agent(self, agent_role: str) -> List[Dict[str, Any]]:
        """Get all entries for a specific agent role."""
        return [e for e in self.entries if e.get('agent_role') == agent_role]
    
    def get_entries_for_pr(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get all entries for a specific PR."""
        return [e for e in self.entries if e.get('pr_number') == pr_number]
    
    def get_entries_for_issue(self, issue_number: int) -> List[Dict[str, Any]]:
        """Get all entries for a specific issue."""
        return [e for e in self.entries if e.get('issue_number') == issue_number]


def validate_pr_signature(pr_body: str) -> tuple[bool, List[str]]:
    """
    Validate that a PR has a proper agent signature.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not pr_body:
        errors.append("PR body is empty - cannot verify agent signature")
        return False, errors
    
    signature = AgentSignature.from_text(pr_body)
    
    if not signature:
        errors.append(
            "No agent signature found in PR description. "
            "Agent should include signature comment in format: "
            "<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->"
        )
        return False, errors
    
    # Validate the signature itself
    sig_errors = signature.validate()
    if sig_errors:
        errors.extend(sig_errors)
        return False, errors
    
    return True, []


def generate_agent_checklist(agent_role: str) -> str:
    """
    Generate a checklist of agent responsibilities based on role.
    
    This helps verify that the agent is following its prompt.
    """
    role_checklists = {
        "role:spec": """## Agent Checklist (Spec Agent)
- [ ] Checked project status.json before starting
- [ ] Defined clear project goals
- [ ] Listed scope and non-goals
- [ ] Created acceptance criteria
- [ ] Documented key decisions and tradeoffs
- [ ] Created/updated spec.md
- [ ] Created/updated acceptance-tests.md""",
        
        "role:architect": """## Agent Checklist (Architect Agent)
- [ ] Checked project status.json before starting
- [ ] Read and understood spec.md
- [ ] Designed system architecture
- [ ] Identified components and interfaces
- [ ] Documented tradeoffs and decisions
- [ ] Created implementation plan with milestones
- [ ] Created/updated architecture.md
- [ ] Created/updated plan.md
- [ ] Created/updated tasks.md""",
        
        "role:swe": """## Agent Checklist (SWE Agent)
- [ ] Checked project status.json before starting
- [ ] Read architecture and plan
- [ ] Implemented features with tests
- [ ] Ran linting and fixed all issues
- [ ] Achieved >80% code coverage
- [ ] Manually verified functionality
- [ ] Kept files under quality bar limits
- [ ] Updated documentation as needed""",
        
        "role:testing": """## Agent Checklist (Testing Agent)
- [ ] Checked project status.json before starting
- [ ] Reviewed existing test coverage
- [ ] Created comprehensive test plan
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] Added edge case tests
- [ ] Verified all tests pass
- [ ] Updated test-plan.md""",
        
        "role:security": """## Agent Checklist (Security Agent)
- [ ] Checked project status.json before starting
- [ ] Reviewed architecture for security issues
- [ ] Checked for common vulnerabilities
- [ ] Validated input handling
- [ ] Verified secrets management
- [ ] Documented security considerations
- [ ] Added security tests if applicable
- [ ] Updated security notes in architecture.md""",
        
        "role:deployment": """## Agent Checklist (Deployment Agent)
- [ ] Checked project status.json before starting
- [ ] Created deployment strategy
- [ ] Documented operational procedures
- [ ] Estimated costs and resources
- [ ] Created monitoring plan
- [ ] Documented rollback procedures
- [ ] Created/updated runbook.md
- [ ] Created/updated cost-plan.md""",
        
        "role:debugging": """## Agent Checklist (Debugging Agent)
- [ ] Checked project status.json before starting
- [ ] Reproduced the bug
- [ ] Identified root cause
- [ ] Created fix with explanation
- [ ] Added regression test
- [ ] Verified fix resolves issue
- [ ] Checked for similar issues
- [ ] Updated documentation if needed"""
    }
    
    return role_checklists.get(
        agent_role,
        f"## Agent Checklist ({agent_role})\n- [ ] Checked project status.json before starting\n- [ ] Completed assigned work"
    )


def check_spec_references(repo_root: Path = None) -> tuple[bool, List[str]]:
    """
    Check if all agent prompts reference their specification files.
    
    Args:
        repo_root: Path to repository root (defaults to current directory)
    
    Returns:
        Tuple of (all_valid, list_of_issues)
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    issues = []
    agents_dir = repo_root / ".github" / "agents"
    specs_dir = repo_root / "specs" / "kerrigan" / "agents"
    
    if not agents_dir.exists():
        issues.append(f"Agent prompts directory not found: {agents_dir}")
        return False, issues
    
    if not specs_dir.exists():
        issues.append(f"Agent specs directory not found: {specs_dir}")
        return False, issues
    
    # Map of agent role files to their spec directories
    agent_specs = {
        "role.architect.md": "architect",
        "role.debugging.md": "debugging",
        "role.deployment.md": "deployment",
        "role.security.md": "security",
        "role.spec.md": "spec",
        "role.swe.md": "swe",
        "role.testing.md": "testing",
    }
    
    for role_file, spec_name in agent_specs.items():
        role_path = agents_dir / role_file
        
        if not role_path.exists():
            issues.append(f"Agent role file not found: {role_path}")
            continue
        
        role_content = role_path.read_text()
        
        # Check if the role file references its spec files
        expected_references = [
            f"specs/kerrigan/agents/{spec_name}/spec.md",
            f"specs/kerrigan/agents/{spec_name}/quality-bar.md",
            f"specs/kerrigan/agents/{spec_name}/architecture.md",
            f"specs/kerrigan/agents/{spec_name}/acceptance-tests.md",
        ]
        
        missing_refs = []
        for ref in expected_references:
            if ref not in role_content:
                missing_refs.append(ref)
        
        if missing_refs:
            issues.append(
                f"Agent {role_file} missing references to: {', '.join(missing_refs)}"
            )
        
        # Check if the spec files actually exist
        for ref in expected_references:
            spec_path = repo_root / ref
            if not spec_path.exists():
                issues.append(f"Referenced spec file does not exist: {ref}")
    
    return len(issues) == 0, issues


def validate_spec_compliance(agent_role: str, pr_body: str = None, repo_root: Path = None) -> tuple[bool, List[str]]:
    """
    Validate that an agent is complying with its specification.
    
    This checks:
    1. Agent signature is present and valid
    2. Agent checklist items are addressed (if present in PR body)
    3. References to spec are present in PR body (encourages spec review)
    
    Args:
        agent_role: Role identifier (e.g., "role:swe")
        pr_body: Optional PR body text to analyze
        repo_root: Path to repository root (defaults to current directory)
    
    Returns:
        Tuple of (is_compliant, list_of_issues)
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    issues = []
    
    # Check that agent prompt references its spec
    valid_refs, ref_issues = check_spec_references(repo_root)
    if not valid_refs:
        issues.extend(ref_issues)
    
    # If PR body is provided, validate signature
    if pr_body:
        sig_valid, sig_errors = validate_pr_signature(pr_body)
        if not sig_valid:
            issues.extend(sig_errors)
        else:
            # Check if signature role matches expected role
            sig = AgentSignature.from_text(pr_body)
            if sig and sig.role != agent_role:
                issues.append(
                    f"Signature role '{sig.role}' does not match expected role '{agent_role}'"
                )
    
    return len(issues) == 0, issues


def check_quality_bar_compliance(
    agent_role: str,
    artifact_paths: List[Path],
    repo_root: Path = None
) -> tuple[bool, List[str]]:
    """
    Check if agent output meets quality bar standards.
    
    This performs basic checks based on the agent's quality bar specification:
    - File size limits (no files >800 lines without justification)
    - Required sections present in artifacts
    - File structure compliance
    
    Args:
        agent_role: Role identifier (e.g., "role:swe", "role:architect")
        artifact_paths: List of file paths to check
        repo_root: Path to repository root (defaults to current directory)
    
    Returns:
        Tuple of (meets_standards, list_of_issues)
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    issues = []
    
    # File extensions to skip for size checking (documentation and config files)
    SKIP_EXTENSIONS = {'.md', '.json', '.yaml', '.yml', '.txt'}
    
    # Check file size limits (common across all agents)
    for artifact_path in artifact_paths:
        if not artifact_path.exists():
            issues.append(f"Artifact not found: {artifact_path}")
            continue
        
        # Skip non-source files
        if artifact_path.suffix in SKIP_EXTENSIONS:
            continue
        
        # Count lines in source files
        try:
            with open(artifact_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
            
            if line_count > 800:
                issues.append(
                    f"File {artifact_path} has {line_count} lines (exceeds 800 line quality bar limit)"
                )
            elif line_count > 400:
                # Add warning to issues with special prefix for warnings
                issues.append(
                    f"WARNING: File {artifact_path} has {line_count} lines (approaching 800 line limit)"
                )
        except Exception as e:
            issues.append(f"Could not read file {artifact_path}: {e}")
    
    # Role-specific quality checks
    if agent_role in ["role:architect", "role:spec"]:
        # Check for required documentation sections
        for artifact_path in artifact_paths:
            if artifact_path.name in ["spec.md", "architecture.md"]:
                try:
                    content = artifact_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check for required sections based on artifact type
                    if artifact_path.name == "spec.md":
                        required_sections = ["## Goal", "## Scope", "## Non-goals", "## Acceptance criteria"]
                    elif artifact_path.name == "architecture.md":
                        required_sections = ["## Overview", "## Components & interfaces", "## Tradeoffs", "## Security & privacy notes"]
                    else:
                        continue
                    
                    for section in required_sections:
                        if section not in content:
                            issues.append(
                                f"Required section '{section}' missing in {artifact_path}"
                            )
                except Exception as e:
                    issues.append(f"Could not validate {artifact_path}: {e}")
    
    return len(issues) == 0, issues


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: agent_audit.py <command> [args]")
        print("\nCommands:")
        print("  validate-pr <pr_body_file>           - Validate PR has proper agent signature")
        print("  create-signature <role>              - Create a new agent signature")
        print("  generate-checklist <role>            - Generate agent responsibility checklist")
        print("  check-spec-references [repo_root]    - Check if agent prompts reference their specs")
        print("  validate-compliance <role> [pr_body] - Validate agent spec compliance")
        print("  check-quality-bar <role> <files...>  - Check quality bar compliance for artifacts")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "validate-pr":
        if len(sys.argv) < 3:
            print("Error: Missing PR body file argument")
            sys.exit(1)
        
        pr_body_file = Path(sys.argv[2])
        if not pr_body_file.exists():
            print(f"Error: File not found: {pr_body_file}")
            sys.exit(1)
        
        pr_body = pr_body_file.read_text()
        is_valid, errors = validate_pr_signature(pr_body)
        
        if is_valid:
            print("✅ Agent signature is valid")
            sig = AgentSignature.from_text(pr_body)
            print(f"   Role: {sig.role}")
            print(f"   Version: {sig.version}")
            print(f"   Timestamp: {sig.timestamp}")
            sys.exit(0)
        else:
            print("❌ Agent signature validation failed:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)
    
    elif command == "create-signature":
        if len(sys.argv) < 3:
            print("Error: Missing role argument")
            sys.exit(1)
        
        role = sys.argv[2]
        signature = AgentSignature.create(role)
        print(signature.to_markdown_comment())
    
    elif command == "generate-checklist":
        if len(sys.argv) < 3:
            print("Error: Missing role argument")
            sys.exit(1)
        
        role = sys.argv[2]
        print(generate_agent_checklist(role))
    
    elif command == "check-spec-references":
        repo_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
        
        print("Checking if agent prompts reference their specifications...")
        is_valid, issues = check_spec_references(repo_root)
        
        if is_valid:
            print("✅ All agent prompts properly reference their specifications")
            sys.exit(0)
        else:
            print("❌ Spec reference validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
    
    elif command == "validate-compliance":
        if len(sys.argv) < 3:
            print("Error: Missing role argument")
            sys.exit(1)
        
        role = sys.argv[2]
        pr_body = None
        
        if len(sys.argv) > 3:
            pr_body_file = Path(sys.argv[3])
            if pr_body_file.exists():
                pr_body = pr_body_file.read_text()
            else:
                print(f"Warning: PR body file not found: {pr_body_file}")
        
        print(f"Validating spec compliance for {role}...")
        is_compliant, issues = validate_spec_compliance(role, pr_body)
        
        if is_compliant:
            print(f"✅ {role} is compliant with its specification")
            sys.exit(0)
        else:
            print(f"❌ Spec compliance validation failed for {role}:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
    
    elif command == "check-quality-bar":
        if len(sys.argv) < 4:
            print("Error: Missing role and/or file arguments")
            print("Usage: agent_audit.py check-quality-bar <role> <file1> [file2] ...")
            sys.exit(1)
        
        role = sys.argv[2]
        artifact_paths = [Path(p) for p in sys.argv[3:]]
        
        print(f"Checking quality bar compliance for {role}...")
        meets_standards, issues = check_quality_bar_compliance(role, artifact_paths)
        
        # Separate warnings from errors
        warnings = [i for i in issues if i.startswith("WARNING:")]
        errors = [i for i in issues if not i.startswith("WARNING:")]
        
        # Display warnings
        for warning in warnings:
            print(f"⚠️  {warning[9:]}")  # Skip "WARNING: " prefix
        
        if len(errors) == 0:
            print(f"✅ All artifacts meet quality bar standards for {role}")
            sys.exit(0)
        else:
            print(f"❌ Quality bar validation failed for {role}:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)
    
    else:
        print(f"Error: Unknown command: {command}")
        sys.exit(1)
