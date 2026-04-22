#!/usr/bin/env python3
"""Read unresolved review comments from a GitHub PR.

Usage: python tools/pr_comments.py [PR_NUMBER]

Requires: gh CLI authenticated.
"""

import json
import subprocess
import sys


def get_repo_slug() -> str:
    """Detect owner/repo from git remote."""
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return result.stdout.strip()


def get_review_comments(pr_number: int) -> list[dict]:
    """Fetch all review comments for a PR (handles pagination)."""
    slug = get_repo_slug()
    result = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{slug}/pulls/{pr_number}/comments"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return json.loads(result.stdout)


def _fetch_all_threads(owner: str, name: str, pr_number: int) -> list[dict]:
    """Fetch all review threads via GraphQL with cursor pagination."""
    all_threads: list[dict] = []
    cursor = None
    while True:
        after = f', after: "{cursor}"' if cursor else ""
        query = (
            '{ repository(owner: "' + owner + '", name: "' + name + '") '
            '{ pullRequest(number: ' + str(pr_number) + ') '
            '{ reviewThreads(first: 50' + after + ') { pageInfo { hasNextPage endCursor } '
            'nodes { id isResolved '
            'comments(first: 100) { nodes { id } } } } } } }'
        )
        result = subprocess.run(
            ["gh", "api", "graphql", "-f", f"query={query}"],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
        data = json.loads(result.stdout)
        page = data["data"]["repository"]["pullRequest"]["reviewThreads"]
        all_threads.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return all_threads


def get_unresolved_thread_ids(pr_number: int, slug: str) -> set[str]:
    """Get IDs of unresolved review threads via GraphQL."""
    owner, name = slug.split("/")
    threads = _fetch_all_threads(owner, name, pr_number)
    unresolved_comment_ids = set()
    for t in threads:
        if not t["isResolved"]:
            for c in t["comments"]["nodes"]:
                unresolved_comment_ids.add(c["id"])
    return unresolved_comment_ids


def resolve_threads(pr_number: int) -> int:
    """Resolve all unresolved review threads. Returns count resolved."""
    slug = get_repo_slug()
    owner, name = slug.split("/")
    threads = _fetch_all_threads(owner, name, pr_number)
    count = 0
    for t in threads:
        if not t["isResolved"]:
            mutation = (
                'mutation { resolveReviewThread(input: {threadId: "'
                + t["id"]
                + '"}) { thread { id isResolved } } }'
            )
            subprocess.run(
                ["gh", "api", "graphql", "-f", f"query={mutation}"],
                capture_output=True, text=True, encoding="utf-8", check=True,
            )
            count += 1
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/pr_comments.py <PR_NUMBER> [--resolve]")
        sys.exit(1)

    pr_number = int(sys.argv[1])
    do_resolve = "--resolve" in sys.argv

    if do_resolve:
        count = resolve_threads(pr_number)
        print(f"Resolved {count} thread(s).")
        return

    slug = get_repo_slug()
    comments = get_review_comments(pr_number)
    unresolved_ids = get_unresolved_thread_ids(pr_number, slug)

    # Map comment node_id to resolved status
    unresolved = [c for c in comments if c.get("node_id") in unresolved_ids]
    resolved = [c for c in comments if c.get("node_id") not in unresolved_ids]

    if unresolved:
        print(f"=== {len(unresolved)} UNRESOLVED comment(s) ===\n")
        for c in sorted(unresolved, key=lambda x: x["created_at"]):
            print(f"  {c['path']}:{c.get('line', '?')}")
            # Print first 5 lines of body
            lines = c["body"].strip().split("\n")
            for line in lines[:5]:
                print(f"    {line[:150]}")
            if len(lines) > 5:
                print(f"    ... ({len(lines) - 5} more lines)")
            print()
    else:
        print("No unresolved comments.")

    if resolved:
        print(f"=== {len(resolved)} resolved comment(s) (skipped) ===")


if __name__ == "__main__":
    main()
