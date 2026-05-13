---
name: Dev10x-gh-pr-request-review
description: Request review on a GitHub PR from teams or users
---

Request reviews on GitHub pull requests from teams or individual users.
Use the GitHub reviewer-assignment MCP tool. Do not call the removed
`$HOME/.codex/tools/gh-request-review.py` helper.

## Usage

### Request review from a team

```text
mcp__plugin_Dev10x_cli__request_review(
    pr_number=PR_NUMBER,
    reviewers=["org-name/team-slug"],
    team=true)
```

### Request review from a user

```text
mcp__plugin_Dev10x_cli__request_review(
    pr_number=PR_NUMBER,
    reviewers=["username"])
```

### Request review from multiple reviewers

```text
mcp__plugin_Dev10x_cli__request_review(
    pr_number=PR_NUMBER,
    reviewers=["user1", "user2"])
```

### With verification

```bash
gh pr view PR_NUMBER --json reviewRequests \
  --jq '.reviewRequests[].login // .reviewRequests[].name'
```

## Notes

- Use `mcp__plugin_Dev10x_cli__request_review` for reviewer assignment
- Team format: `org-name/team-slug`
- Mixed user and team requests require separate calls
- Verify the review request was assigned by checking `reviewRequests`
