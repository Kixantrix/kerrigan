#!/usr/bin/env python3
"""Task dependency validator for Kerrigan.

Validates task dependencies in tasks.md files:
- Syntax validation (proper format for dependency references)
- Cycle detection (no circular dependencies)
- Optional: reference validation (issues exist in target repos)

Design philosophy: Enable parallel agent work through explicit dependency tracking.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs" / "projects"

# Task section names to recognize
TASK_SECTIONS = ["Done when", "Links", "Status", "Dependencies", "Blocks"]

# Directories to exclude from validation
EXCLUDED_DIRS = ["_template", "_archive", "tests", "test", "test-project", 
                 "pause-resume-demo"]


@dataclass
class Dependency:
    """Represents a task dependency."""
    raw: str
    is_soft: bool
    dep_type: str  # 'same-repo', 'cross-repo', 'local-task', 'external'
    owner: str | None
    repo: str | None
    issue_num: int | None
    description: str | None

    def target_id(self) -> str:
        """Return unique identifier for this dependency."""
        if self.dep_type == 'same-repo':
            return f"#{self.issue_num}"
        elif self.dep_type == 'cross-repo':
            return f"{self.owner}/{self.repo}#{self.issue_num}"
        elif self.dep_type == 'local-task':
            return f"{self.repo}:#{self.issue_num}"
        else:  # external
            return f"external:{self.description}"


@dataclass
class Task:
    """Represents a task with its dependencies."""
    id: str  # Issue number or unique identifier
    title: str
    dependencies: List[Dependency]
    blocks: List[Dependency]
    line_num: int


def fail(msg: str) -> None:
    """Print error and exit."""
    print(f"::error::{msg}")
    raise SystemExit(1)


def warn(msg: str) -> None:
    """Print warning."""
    print(f"::warning::{msg}")


def parse_dependency(raw: str) -> Dependency | None:
    """Parse a dependency string into structured format.
    
    Formats:
    - #123 (same repo)
    - owner/repo#123 (cross-repo)
    - repo-name:#123 (local task in multi-repo)
    - external:description (external dependency)
    - ~ prefix for soft dependencies
    """
    raw = raw.strip()
    is_soft = raw.startswith('~')
    if is_soft:
        raw = raw[1:].strip()
    
    # Extract description in parentheses if present
    desc_match = re.search(r'\s*\([^)]+\)\s*$', raw)
    if desc_match:
        raw = raw[:desc_match.start()].strip()
    
    # Match patterns
    # Cross-repo: owner/repo#123
    cross_repo_match = re.match(r'^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)#(\d+)$', raw)
    if cross_repo_match:
        owner, repo, issue_num = cross_repo_match.groups()
        return Dependency(
            raw=raw,
            is_soft=is_soft,
            dep_type='cross-repo',
            owner=owner,
            repo=repo,
            issue_num=int(issue_num),
            description=None
        )
    
    # Local task: repo-name:#123
    local_task_match = re.match(r'^([a-zA-Z0-9_-]+):#(\d+)$', raw)
    if local_task_match:
        repo, issue_num = local_task_match.groups()
        return Dependency(
            raw=raw,
            is_soft=is_soft,
            dep_type='local-task',
            owner=None,
            repo=repo,
            issue_num=int(issue_num),
            description=None
        )
    
    # Same repo: #123
    same_repo_match = re.match(r'^#(\d+)$', raw)
    if same_repo_match:
        issue_num = same_repo_match.group(1)
        return Dependency(
            raw=raw,
            is_soft=is_soft,
            dep_type='same-repo',
            owner=None,
            repo=None,
            issue_num=int(issue_num),
            description=None
        )
    
    # External: external:description
    external_match = re.match(r'^external:(.+)$', raw)
    if external_match:
        description = external_match.group(1).strip()
        return Dependency(
            raw=raw,
            is_soft=is_soft,
            dep_type='external',
            owner=None,
            repo=None,
            issue_num=None,
            description=description
        )
    
    return None


def extract_tasks_from_file(tasks_file: Path) -> List[Task]:
    """Extract tasks with dependencies from tasks.md file."""
    if not tasks_file.exists():
        return []
    
    content = tasks_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    tasks = []
    current_task = None
    in_dependencies = False
    in_blocks = False
    
    for i, line in enumerate(lines, 1):
        # Match task line: - [ ] Task: description
        task_match = re.match(r'^-\s*\[\s*\]\s*Task:\s*(.+)$', line)
        if task_match:
            if current_task:
                tasks.append(current_task)
            
            title = task_match.group(1).strip()
            # Try to extract issue number from title or use title as ID
            issue_match = re.search(r'#(\d+)', title)
            task_id = f"#{issue_match.group(1)}" if issue_match else title
            
            current_task = Task(
                id=task_id,
                title=title,
                dependencies=[],
                blocks=[],
                line_num=i
            )
            in_dependencies = False
            in_blocks = False
            continue
        
        if not current_task:
            continue
        
        # Check for Dependencies section
        if re.match(r'^\s*-?\s*Dependencies:\s*$', line):
            in_dependencies = True
            in_blocks = False
            continue
        
        # Check for Blocks section
        if re.match(r'^\s*-?\s*Blocks:\s*$', line):
            in_blocks = True
            in_dependencies = False
            continue
        
        # Check for other sections (Done when, Links, etc.)
        if any(re.match(rf'^\s*-\s*{section}:', line) for section in TASK_SECTIONS):
            in_dependencies = False
            in_blocks = False
            continue
        
        # Parse dependency/block items
        dep_line_match = re.match(r'^\s*-\s*(.+)$', line)
        if dep_line_match and (in_dependencies or in_blocks):
            dep_raw = dep_line_match.group(1).strip()
            dep = parse_dependency(dep_raw)
            
            if dep:
                if in_dependencies:
                    current_task.dependencies.append(dep)
                elif in_blocks:
                    current_task.blocks.append(dep)
            else:
                warn(f"{tasks_file.name}:{i} - Invalid dependency format: {dep_raw}")
    
    if current_task:
        tasks.append(current_task)
    
    return tasks


def build_dependency_graph(tasks: List[Task]) -> Dict[str, List[str]]:
    """Build adjacency list representation of task dependencies.
    
    Only includes hard dependencies (soft dependencies are excluded from graph).
    """
    graph = {}
    
    # Initialize all task nodes
    for task in tasks:
        graph[task.id] = []
    
    # Add edges (dependency -> dependent)
    for task in tasks:
        for dep in task.dependencies:
            if not dep.is_soft:  # Only hard dependencies create edges
                dep_id = dep.target_id()
                if dep_id not in graph:
                    graph[dep_id] = []
                graph[dep_id].append(task.id)
    
    return graph


def detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detect cycles in dependency graph using DFS with color marking.
    
    Returns list of cycles, where each cycle is a list of task IDs.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    cycles = []
    path = []
    
    def dfs(node: str) -> bool:
        if color.get(node, WHITE) == GRAY:
            # Found a cycle
            if node in path:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
            else:
                # Unexpected: node marked GRAY but not in path
                warn(f"Unexpected cycle detection state for node {node}")
            return True
        
        if color.get(node, WHITE) == BLACK:
            return False
        
        color[node] = GRAY
        path.append(node)
        
        for neighbor in graph.get(node, []):
            dfs(neighbor)
        
        path.pop()
        color[node] = BLACK
        return False
    
    for node in graph:
        if color[node] == WHITE:
            dfs(node)
    
    return cycles


def validate_cycles(tasks: List[Task], project_name: str) -> bool:
    """Validate no circular dependencies exist."""
    if not tasks:
        return True
    
    graph = build_dependency_graph(tasks)
    cycles = detect_cycles(graph)
    
    if cycles:
        error_msg = f"Project '{project_name}' has circular dependencies:\n"
        for i, cycle in enumerate(cycles, 1):
            cycle_str = " -> ".join(cycle)
            error_msg += f"  Cycle {i}: {cycle_str}\n"
        error_msg += "\nResolution: Remove one dependency to break each cycle."
        fail(error_msg)
        return False
    
    return True


def validate_project_dependencies(project_dir: Path) -> bool:
    """Validate dependencies for a single project."""
    tasks_file = project_dir / "tasks.md"
    if not tasks_file.exists():
        return True  # No tasks file, nothing to validate
    
    project_name = project_dir.name
    tasks = extract_tasks_from_file(tasks_file)
    
    if not tasks:
        return True  # No tasks with dependencies
    
    # Validate no cycles (syntax is validated during parsing)
    if not validate_cycles(tasks, project_name):
        return False
    
    return True


def project_folders() -> List[Path]:
    """Get list of project folders to validate."""
    if not SPECS_DIR.exists():
        return []
    
    return [p for p in SPECS_DIR.iterdir() 
            if p.is_dir() and p.name not in EXCLUDED_DIRS]


def main() -> None:
    """Main entry point for dependency validation."""
    projects = project_folders()
    
    if not projects:
        print("No projects found to validate.")
        return
    
    all_valid = True
    for project_dir in projects:
        if not validate_project_dependencies(project_dir):
            all_valid = False
    
    if all_valid:
        print("Dependency checks passed.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
