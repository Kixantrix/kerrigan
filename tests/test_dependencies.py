#!/usr/bin/env python3
"""Tests for task dependency validator."""

import sys
import tempfile
from pathlib import Path

# Import validator module
REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "tools" / "validators"
if str(VALIDATOR_PATH) not in sys.path:
    sys.path.insert(0, str(VALIDATOR_PATH))

from check_dependencies import (
    Dependency,
    Task,
    parse_dependency,
    build_dependency_graph,
    detect_cycles,
    extract_tasks_from_file,
)


def test_parse_dependency_same_repo():
    """Test parsing same-repo dependency."""
    dep = parse_dependency("#123")
    assert dep is not None
    assert dep.dep_type == 'same-repo'
    assert dep.issue_num == 123
    assert not dep.is_soft


def test_parse_dependency_cross_repo():
    """Test parsing cross-repo dependency."""
    dep = parse_dependency("Kixantrix/kerrigan#42")
    assert dep is not None
    assert dep.dep_type == 'cross-repo'
    assert dep.owner == "Kixantrix"
    assert dep.repo == "kerrigan"
    assert dep.issue_num == 42


def test_parse_dependency_local_task():
    """Test parsing local task dependency."""
    dep = parse_dependency("api:#15")
    assert dep is not None
    assert dep.dep_type == 'local-task'
    assert dep.repo == "api"
    assert dep.issue_num == 15


def test_parse_dependency_external():
    """Test parsing external dependency."""
    dep = parse_dependency("external:legal approval required")
    assert dep is not None
    assert dep.dep_type == 'external'
    assert dep.description == "legal approval required"


def test_parse_dependency_soft():
    """Test parsing soft dependency."""
    dep = parse_dependency("~#456")
    assert dep is not None
    assert dep.is_soft
    assert dep.dep_type == 'same-repo'
    assert dep.issue_num == 456


def test_parse_dependency_with_description():
    """Test parsing dependency with description."""
    dep = parse_dependency("#123 (database schema complete)")
    assert dep is not None
    assert dep.dep_type == 'same-repo'
    assert dep.issue_num == 123


def test_parse_dependency_invalid():
    """Test parsing invalid dependency formats."""
    assert parse_dependency("invalid") is None
    assert parse_dependency("123") is None
    assert parse_dependency("#") is None
    assert parse_dependency("repo#") is None


def test_detect_cycles_no_cycle():
    """Test cycle detection with no cycles."""
    graph = {
        "#1": ["#2", "#3"],
        "#2": ["#4"],
        "#3": ["#4"],
        "#4": []
    }
    cycles = detect_cycles(graph)
    assert len(cycles) == 0


def test_detect_cycles_simple_cycle():
    """Test cycle detection with simple cycle."""
    graph = {
        "#1": ["#2"],
        "#2": ["#3"],
        "#3": ["#1"]
    }
    cycles = detect_cycles(graph)
    assert len(cycles) >= 1
    # Check that a cycle was found involving these nodes
    cycle = cycles[0]
    assert "#1" in cycle
    assert "#2" in cycle
    assert "#3" in cycle


def test_detect_cycles_self_loop():
    """Test cycle detection with self-loop."""
    graph = {
        "#1": ["#1"]
    }
    cycles = detect_cycles(graph)
    assert len(cycles) >= 1


def test_extract_tasks_basic():
    """Test extracting tasks from markdown."""
    content = """# Tasks: test-project

- [ ] Task: First task
  - Done when: Complete
  - Dependencies:
    - #42 (prerequisite)
    - api:#15 (API ready)
  - Blocks:
    - #50 (next task)

- [ ] Task: Second task
  - Done when: Also complete
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        tasks = extract_tasks_from_file(temp_path)
        assert len(tasks) == 2
        
        task1 = tasks[0]
        assert "First task" in task1.title
        assert len(task1.dependencies) == 2
        assert len(task1.blocks) == 1
        
        task2 = tasks[1]
        assert "Second task" in task2.title
        assert len(task2.dependencies) == 0
    finally:
        temp_path.unlink()


def test_extract_tasks_soft_dependencies():
    """Test extracting soft dependencies."""
    content = """# Tasks: test-project

- [ ] Task: Task with soft deps
  - Dependencies:
    - #42 (hard dependency)
    - ~#43 (soft dependency)
    - ~api:#44 (another soft dep)
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        temp_path = Path(f.name)
    
    try:
        tasks = extract_tasks_from_file(temp_path)
        assert len(tasks) == 1
        
        task = tasks[0]
        assert len(task.dependencies) == 3
        
        # First should be hard
        assert not task.dependencies[0].is_soft
        # Others should be soft
        assert task.dependencies[1].is_soft
        assert task.dependencies[2].is_soft
    finally:
        temp_path.unlink()


def test_build_dependency_graph():
    """Test building dependency graph from tasks."""
    tasks = [
        Task(
            id="#1",
            title="Task 1",
            dependencies=[],
            blocks=[],
            line_num=1
        ),
        Task(
            id="#2",
            title="Task 2",
            dependencies=[
                Dependency(
                    raw="#1",
                    is_soft=False,
                    dep_type='same-repo',
                    owner=None,
                    repo=None,
                    issue_num=1,
                    description=None
                )
            ],
            blocks=[],
            line_num=5
        ),
        Task(
            id="#3",
            title="Task 3",
            dependencies=[
                Dependency(
                    raw="#1",
                    is_soft=False,
                    dep_type='same-repo',
                    owner=None,
                    repo=None,
                    issue_num=1,
                    description=None
                )
            ],
            blocks=[],
            line_num=10
        )
    ]
    
    graph = build_dependency_graph(tasks)
    
    # #1 should point to #2 and #3 (they depend on #1)
    assert "#2" in graph["#1"]
    assert "#3" in graph["#1"]
    
    # #2 and #3 should have no dependents
    assert len(graph["#2"]) == 0
    assert len(graph["#3"]) == 0


def test_build_dependency_graph_excludes_soft():
    """Test that soft dependencies are excluded from graph."""
    tasks = [
        Task(
            id="#1",
            title="Task 1",
            dependencies=[],
            blocks=[],
            line_num=1
        ),
        Task(
            id="#2",
            title="Task 2",
            dependencies=[
                Dependency(
                    raw="~#1",
                    is_soft=True,  # Soft dependency
                    dep_type='same-repo',
                    owner=None,
                    repo=None,
                    issue_num=1,
                    description=None
                )
            ],
            blocks=[],
            line_num=5
        )
    ]
    
    graph = build_dependency_graph(tasks)
    
    # Soft dependency should not create edge in graph
    assert "#2" not in graph["#1"]


def run_tests():
    """Run all tests."""
    tests = [
        ("Parse same-repo dependency", test_parse_dependency_same_repo),
        ("Parse cross-repo dependency", test_parse_dependency_cross_repo),
        ("Parse local task dependency", test_parse_dependency_local_task),
        ("Parse external dependency", test_parse_dependency_external),
        ("Parse soft dependency", test_parse_dependency_soft),
        ("Parse dependency with description", test_parse_dependency_with_description),
        ("Parse invalid dependency", test_parse_dependency_invalid),
        ("Detect cycles - no cycle", test_detect_cycles_no_cycle),
        ("Detect cycles - simple cycle", test_detect_cycles_simple_cycle),
        ("Detect cycles - self loop", test_detect_cycles_self_loop),
        ("Extract tasks basic", test_extract_tasks_basic),
        ("Extract tasks with soft dependencies", test_extract_tasks_soft_dependencies),
        ("Build dependency graph", test_build_dependency_graph),
        ("Build dependency graph excludes soft", test_build_dependency_graph_excludes_soft),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
