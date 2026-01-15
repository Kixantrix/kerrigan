#!/usr/bin/env python3
"""Validator for agent signatures in PRs.

This script checks that PRs created by agents include proper signatures
to ensure agents are following their prompts.

This validator is designed to be lightweight and only enforces signatures
on PRs that have agent-related labels.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add parent directory to path to import agent_audit module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_audit import AgentSignature, validate_pr_signature


def main() -> None:
    """Validate agent signature in PR (when run in CI context)."""
    
    # This validator is designed to run in GitHub Actions
    # It checks for agent signatures when PR has agent/role labels
    
    # For now, we'll make this informational only since it requires
    # GitHub context that may not always be available
    # In a real CI environment, we'd check GITHUB_EVENT_PATH
    
    github_event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    if not github_event_path:
        print("ℹ️  GITHUB_EVENT_PATH not set - skipping agent signature validation")
        print("   This check only runs in GitHub Actions PR context")
        return
    
    import json
    
    try:
        with open(github_event_path, 'r') as f:
            event_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️  Could not load GitHub event data: {e}")
        return
    
    # Check if this is a PR event
    if 'pull_request' not in event_data:
        print("ℹ️  Not a pull request event - skipping agent signature validation")
        return
    
    pr = event_data['pull_request']
    pr_number = pr.get('number')
    pr_body = pr.get('body', '')
    pr_labels = [label['name'] for label in pr.get('labels', [])]
    
    print(f"🔍 Checking agent signature for PR #{pr_number}")
    print(f"   Labels: {', '.join(pr_labels) if pr_labels else '(none)'}")
    
    # Check if PR has agent or role labels
    agent_labels = [l for l in pr_labels if l.startswith('role:') or l.startswith('agent:')]
    
    if not agent_labels:
        print("ℹ️  No agent/role labels found - skipping signature validation")
        print("   Agent signatures are only required for agent-labeled PRs")
        return
    
    print(f"   Agent labels found: {', '.join(agent_labels)}")
    print("   Validating agent signature...")
    
    # Validate the signature
    is_valid, errors = validate_pr_signature(pr_body)
    
    if is_valid:
        signature = AgentSignature.from_text(pr_body)
        print(f"✅ Agent signature is valid")
        print(f"   Role: {signature.role}")
        print(f"   Version: {signature.version}")
        print(f"   Timestamp: {signature.timestamp}")
        
        # Informational: check if signature role matches labels
        if signature.role not in agent_labels:
            print(f"⚠️  Warning: Signature role '{signature.role}' doesn't match PR labels")
            print(f"   PR labels: {', '.join(agent_labels)}")
            print("   This is informational - signature is still valid")
    else:
        print("❌ Agent signature validation failed:")
        for error in errors:
            print(f"   - {error}")
        print("")
        print("Agent-labeled PRs should include a signature in the PR description.")
        print("This helps verify that agents are using their specific prompts.")
        print("")
        print("To add a signature, include this comment in your PR description:")
        print("<!-- AGENT_SIGNATURE: role=role:swe, version=1.0, timestamp=2026-01-15T06:00:00Z -->")
        print("")
        print("See docs/agent-assignment.md for details on agent signatures.")
        
        # Make this a warning, not an error, to keep it lightweight
        print("")
        print("⚠️  This is a warning only - PR can still be merged")
        print("   Consider adding a signature for better auditability")


if __name__ == "__main__":
    main()
