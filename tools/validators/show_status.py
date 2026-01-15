#!/usr/bin/env python3
"""Display status.json information for all projects.

This script reads status.json files from all projects and displays
their current workflow state in a human-readable format.

Useful for CI output and quick status checks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs" / "projects"


def get_project_status(project_dir: Path) -> Optional[Dict[str, Any]]:
    """Read status.json from a project directory, return None if doesn't exist."""
    status_path = project_dir / "status.json"
    if not status_path.exists():
        return None
    
    try:
        with open(status_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"::error::Failed to read {project_dir.name}/status.json: {e}")
        return {"error": str(e)}


def format_status_emoji(status: str) -> str:
    """Return an emoji for the status."""
    emoji_map = {
        "active": "🟢",
        "blocked": "🔴",
        "on-hold": "🟡",
        "completed": "✅",
    }
    return emoji_map.get(status, "❓")


def format_phase_name(phase: str) -> str:
    """Format phase name for display."""
    return phase.replace("-", " ").title()


def main() -> None:
    """Display status for all projects."""
    if not SPECS_DIR.exists():
        print("No projects directory found.")
        return
    
    projects = [p for p in SPECS_DIR.iterdir() 
                if p.is_dir() and p.name != "_template"]
    
    if not projects:
        print("No projects found.")
        return
    
    print("=" * 70)
    print("PROJECT STATUS SUMMARY")
    print("=" * 70)
    
    has_status_files = False
    blocked_projects = []
    
    for project in sorted(projects):
        status_data = get_project_status(project)
        
        if status_data is None:
            continue
        
        has_status_files = True
        
        if "error" in status_data:
            print(f"\n❌ {project.name}")
            print(f"   Error: {status_data['error']}")
            continue
        
        status = status_data.get("status", "unknown")
        phase = status_data.get("current_phase", "unknown")
        last_updated = status_data.get("last_updated", "unknown")
        
        emoji = format_status_emoji(status)
        phase_display = format_phase_name(phase)
        
        print(f"\n{emoji} {project.name}")
        print(f"   Status: {status.upper()}")
        print(f"   Phase: {phase_display}")
        print(f"   Last Updated: {last_updated}")
        
        if status == "blocked":
            blocked_reason = status_data.get("blocked_reason", "No reason provided")
            print(f"   ⚠️  Blocked Reason: {blocked_reason}")
            blocked_projects.append(project.name)
        
        if status == "on-hold":
            print(f"   ⚠️  Work temporarily paused")
        
        if "notes" in status_data and status_data["notes"]:
            notes = status_data["notes"]
            # Truncate long notes for display
            if len(notes) > 100:
                notes = notes[:97] + "..."
            print(f"   Notes: {notes}")
    
    if not has_status_files:
        print("\nNo projects with status.json files found.")
    else:
        print("\n" + "=" * 70)
        
        if blocked_projects:
            print(f"\n⚠️  WARNING: {len(blocked_projects)} project(s) blocked:")
            for proj in blocked_projects:
                print(f"   - {proj}")
            print("\n   Agents MUST NOT proceed with blocked projects.")
        else:
            print("\n✅ No blocked projects. All projects with status can proceed.")
    
    print()


if __name__ == "__main__":
    main()
