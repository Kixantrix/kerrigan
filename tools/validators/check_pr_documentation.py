#!/usr/bin/env python3
"""
Validator to detect potential fabricated or misleading documentation in PRs.

This validator checks for common patterns that indicate documentation may be
simulated rather than factual, such as references to non-existent PRs, 
disproportionate documentation-to-code ratios, and fictional timelines.

Usage:
    python tools/validators/check_pr_documentation.py [--pr-body FILE]

Exit codes:
    0: All checks passed
    1: Warnings found (review recommended but not blocking)
"""

import re
import sys
import os
import argparse
from pathlib import Path


# Configuration constants (can be overridden via environment variables)
LARGE_DOC_THRESHOLD_KB = int(os.environ.get('PR_DOC_LARGE_THRESHOLD_KB', '15'))
DOC_TO_CODE_RATIO_THRESHOLD = int(os.environ.get('PR_DOC_RATIO_THRESHOLD', '10'))


def check_pr_references(text):
    """Check if PR references actually exist by pattern analysis."""
    warnings = []
    
    # Find PR references like "PR #1", "PR #2", etc.
    pr_refs = re.findall(r'PR\s+#(\d+)', text, re.IGNORECASE)
    
    # Check for suspicious sequential PR references in documentation
    if len(pr_refs) >= 3:
        pr_numbers = [int(n) for n in pr_refs]
        # If we see #1, #2, #3, #4 in a row, that's suspicious
        if pr_numbers == list(range(min(pr_numbers), max(pr_numbers) + 1)):
            warnings.append(
                f"⚠️  Found sequential PR references (#1, #2, #3...). "
                f"Verify these PRs actually exist and aren't simulated."
            )
    
    # Check for phrases indicating simulation
    simulation_phrases = [
        (r'created PR #\d+.*approved', 'created PR #X...approved'),
        (r'PR #\d+.*merged', 'PR #X merged'),
        (r'simulated.*workflow', 'simulated workflow'),
        (r'example workflow.*PR', 'example workflow with PR'),
        (r'demonstrates.*creating PRs', 'demonstrates creating PRs'),
    ]
    
    for pattern, description in simulation_phrases:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_text = match.group()[:50]  # First 50 chars of match
            warnings.append(
                f"⚠️  Found phrase indicating simulated workflow: '{matched_text}...'. "
                f"Ensure documentation describes actual work, not fictional examples."
            )
    
    return warnings


def check_timeline_claims(text):
    """Check for suspicious timeline claims."""
    warnings = []
    
    # Look for specific duration claims
    duration_patterns = [
        r'(\d+)\s*hours?.*development',
        r'development.*(\d+)\s*hours?',
        r'took\s+(\d+)\s*hours?',
        r'(\d+)\s*hours?.*total',
    ]
    
    for pattern in duration_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            warnings.append(
                f"⚠️  Found duration claim in documentation. "
                f"Verify this matches actual git history (check commit timestamps)."
            )
            break
    
    # Look for pause/resume claims
    if re.search(r'pause|blocked.*resume', text, re.IGNORECASE):
        if re.search(r'\d+\s*(min|minutes?)', text, re.IGNORECASE):
            warnings.append(
                f"⚠️  Found pause/resume with duration claims. "
                f"Verify these pauses actually occurred in project history."
            )
    
    return warnings


def check_fabrication_markers(text):
    """Check for common markers of fabricated documentation."""
    warnings = []
    
    # Look for agent signatures in documentation (not PR description)
    if 'RUNBOOK' in text.upper() or 'WORKFLOW-PHASES' in text.upper():
        if re.search(r'AGENT_SIGNATURE.*timestamp', text):
            warnings.append(
                f"⚠️  Found agent signatures in workflow documentation. "
                f"Ensure these represent actual work, not simulated phases."
            )
    
    # Look for elaborate phase descriptions
    if re.search(r'Phase \d+:.*Phase \d+:', text, re.DOTALL):
        phase_count = len(re.findall(r'Phase \d+:', text))
        if phase_count >= 4:
            warnings.append(
                f"⚠️  Found {phase_count} phase descriptions. "
                f"Verify this represents actual development phases, not a simulation."
            )
    
    # Look for fictional human review claims
    review_phrases = [
        r'human.*review.*\d+\s*min',
        r'approved.*after.*\d+\s*min',
        r'review.*outcome.*approved',
    ]
    
    for pattern in review_phrases:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(
                f"⚠️  Found specific human review timing claims. "
                f"Verify these reviews actually occurred in PR/issue history."
            )
            break
    
    return warnings


def check_documentation_ratio(repo_path):
    """Check for disproportionate documentation-to-code ratios."""
    warnings = []
    
    # Look for new markdown files in examples/
    examples_path = repo_path / "examples"
    if not examples_path.exists():
        return warnings
    
    # Find newly added documentation (rough heuristic)
    large_docs = []
    for md_file in examples_path.rglob("*.md"):
        size_kb = md_file.stat().st_size / 1024
        if size_kb > LARGE_DOC_THRESHOLD_KB:
            large_docs.append((md_file.name, size_kb))
    
    if large_docs:
        # Check if there's proportional code
        code_files = list(examples_path.rglob("*.py")) + \
                     list(examples_path.rglob("*.js")) + \
                     list(examples_path.rglob("*.go")) + \
                     list(examples_path.rglob("*.rs"))
        
        total_code_kb = sum(f.stat().st_size / 1024 for f in code_files) if code_files else 0
        total_doc_kb = sum(size for _, size in large_docs)
        
        if total_doc_kb > total_code_kb * DOC_TO_CODE_RATIO_THRESHOLD:
            warnings.append(
                f"⚠️  Documentation significantly outweighs code "
                f"({total_doc_kb:.1f}KB docs vs {total_code_kb:.1f}KB code). "
                f"Consider if this is appropriate or if documentation includes simulation."
            )
    
    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="Validate PR documentation for accuracy and detect potential fabrication"
    )
    parser.add_argument(
        "--pr-body",
        help="Path to file containing PR body text to validate"
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to repository root (default: current directory)"
    )
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path).resolve()
    all_warnings = []
    
    # Check PR body if provided
    if args.pr_body:
        pr_body_path = Path(args.pr_body)
        if pr_body_path.exists():
            text = pr_body_path.read_text()
            
            all_warnings.extend(check_pr_references(text))
            all_warnings.extend(check_timeline_claims(text))
            all_warnings.extend(check_fabrication_markers(text))
    
    # Check documentation ratios in repository
    all_warnings.extend(check_documentation_ratio(repo_path))
    
    # Report results
    if all_warnings:
        print("PR Documentation Validation - Warnings Found:")
        print("=" * 70)
        for warning in all_warnings:
            print(warning)
            print()
        print("=" * 70)
        print(f"Total warnings: {len(all_warnings)}")
        print()
        print("These are warnings, not errors. Review the flagged items to ensure")
        print("documentation is factually accurate and doesn't include simulations.")
        print()
        print("See docs/pr-documentation-guidelines.md for standards.")
        return 1
    else:
        print("✅ PR documentation validation passed - no warnings")
        return 0


if __name__ == "__main__":
    sys.exit(main())
