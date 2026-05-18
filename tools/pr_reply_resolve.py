#!/usr/bin/env python3
"""Reply to a PR review comment and resolve its thread.

Usage:
  python tools/pr_reply_resolve.py <pr_number> <comment_id> "reply body"

Looks up the thread containing the given review comment, posts a reply,
then resolves the thread. Used by kerrigan to close out advisory/addressed
review threads with rationale (cloud agents handle code fixes themselves).
"""

import json
import subprocess
import sys


def run_gh(args: list[str]) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True)
    return r.stdout


def repo_slug() -> tuple[str, str]:
    slug = run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).strip()
    owner, name = slug.split("/")
    return owner, name


def find_thread_for_comment(owner: str, name: str, pr: int, comment_db_id: int) -> str:
    query = (
        'query { repository(owner: "' + owner + '", name: "' + name + '") '
        '{ pullRequest(number: ' + str(pr) + ') '
        '{ reviewThreads(first: 100) { nodes { id isResolved '
        'comments(first: 50) { nodes { databaseId } } } } } } }'
    )
    out = run_gh(["api", "graphql", "-f", f"query={query}"])
    data = json.loads(out)["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    for t in data:
        for c in t["comments"]["nodes"]:
            if c["databaseId"] == comment_db_id:
                return t["id"]
    raise SystemExit(f"comment {comment_db_id} not found in any thread on PR #{pr}")


def reply_to_comment(owner: str, name: str, pr: int, comment_id: int, body: str) -> None:
    run_gh([
        "api", "--method", "POST",
        f"repos/{owner}/{name}/pulls/{pr}/comments/{comment_id}/replies",
        "-f", f"body={body}",
    ])


def resolve_thread(thread_node_id: str) -> None:
    mutation = (
        'mutation { resolveReviewThread(input: {threadId: "' + thread_node_id + '"}) '
        '{ thread { id isResolved } } }'
    )
    run_gh(["api", "graphql", "-f", f"query={mutation}"])


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    pr = int(sys.argv[1])
    comment_id = int(sys.argv[2])
    body = sys.argv[3]
    owner, name = repo_slug()
    thread_id = find_thread_for_comment(owner, name, pr, comment_id)
    reply_to_comment(owner, name, pr, comment_id, body)
    resolve_thread(thread_id)
    print(f"PR #{pr}: replied to comment {comment_id} + resolved thread {thread_id}")


if __name__ == "__main__":
    main()
