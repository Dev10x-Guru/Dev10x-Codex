#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Scan merged PRs for unresolved review comment threads.

Uses GitHub REST API to list merged PRs and GraphQL to check
thread resolution status. Skips PRs with audit trail markers.

Output: JSON array of PRs with unresolved threads.
"""

import argparse
import json
import subprocess
import sys

AUDIT_MARKER = "PR Audit"

GRAPHQL_QUERY = """
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          comments(first: 1) {
            nodes {
              body
              author { login }
              path
            }
          }
        }
      }
    }
  }
}
"""


def run_gh(args: list[str]) -> str:
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"gh error: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def fetch_merged_prs(
    repo: str,
    limit: int,
) -> list[dict]:
    output = run_gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--limit",
            str(limit),
            "--json",
            "number,title,mergedAt",
        ]
    )
    if not output:
        return []
    return json.loads(output)


def has_audit_marker(
    repo: str,
    pr_number: int,
) -> bool:
    output = run_gh(
        [
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            "comments",
            "--jq",
            ".comments[].body",
        ]
    )
    return AUDIT_MARKER in output


def fetch_unresolved_threads(
    owner: str,
    repo_name: str,
    pr_number: int,
) -> list[dict]:
    output = run_gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={GRAPHQL_QUERY}",
            "-f",
            f"owner={owner}",
            "-f",
            f"repo={repo_name}",
            "-F",
            f"pr={pr_number}",
        ]
    )
    if not output:
        return []
    data = json.loads(output)
    threads = (
        data.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
        .get("nodes", [])
    )
    unresolved = []
    for thread in threads:
        if thread.get("isResolved"):
            continue
        comments = thread.get("comments", {}).get("nodes", [])
        if not comments:
            continue
        comment = comments[0]
        unresolved.append(
            {
                "path": comment.get("path", ""),
                "body": comment.get("body", "")[:200],
                "author": comment.get("author", {}).get("login", "unknown"),
            }
        )
    return unresolved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan merged PRs for unresolved review threads",
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Max PRs to scan (default: 200)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show findings without side effects",
    )
    args = parser.parse_args()

    owner, repo_name = args.repo.split("/", 1)
    prs = fetch_merged_prs(repo=args.repo, limit=args.limit)

    if not prs:
        print("No merged PRs found.")
        return 0

    print(f"Scanning {len(prs)} merged PRs...", file=sys.stderr)

    findings = []
    clean_count = 0
    skipped_count = 0

    for pr in prs:
        pr_number = pr["number"]

        if has_audit_marker(repo=args.repo, pr_number=pr_number):
            skipped_count += 1
            continue

        threads = fetch_unresolved_threads(
            owner=owner,
            repo_name=repo_name,
            pr_number=pr_number,
        )

        if threads:
            findings.append(
                {
                    "pr_number": pr_number,
                    "title": pr["title"],
                    "threads": threads,
                }
            )
        else:
            clean_count += 1

    print(
        f"Results: {len(findings)} PRs with findings, "
        f"{clean_count} clean, {skipped_count} skipped (already audited)",
        file=sys.stderr,
    )

    print(json.dumps(findings, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
