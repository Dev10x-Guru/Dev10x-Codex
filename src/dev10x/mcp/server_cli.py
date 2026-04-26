"""MCP server registration for the Dev10x CLI server.

All @server.tool() registrations live here so servers/cli_server.py
becomes a thin 3-line uv shim. Tool handlers use lazy imports to
defer domain module loading until each tool is called.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

server = FastMCP(name="Dev10x-cli")


# ── GitHub tools ────────────────────────────────────────────────


@server.tool()
async def detect_tracker(ticket_id: str) -> dict:
    """Detect issue tracker type from a ticket ID.

    Args:
        ticket_id: Ticket identifier (e.g., GH-15, TEAM-133, JIRA-42)

    Returns:
        Dictionary with keys: tracker, ticket_id, ticket_number, fixes_url
    """
    from dev10x.mcp import github as gh

    return gh.detect_tracker(ticket_id=ticket_id)


@server.tool()
async def pr_detect(arg: str) -> dict:
    """Detect PR context from a PR number, URL, or branch name.

    Args:
        arg: PR number (#123), full URL, or branch name

    Returns:
        Dictionary with keys: pr_number, repo, branch, state, head_ref
    """
    from dev10x.mcp import github as gh

    return gh.pr_detect(arg=arg)


@server.tool()
async def issue_get(number: int, repo: str | None = None) -> dict:
    """Get GitHub issue details.

    Args:
        number: Issue number
        repo: Repository (owner/repo). If omitted, uses current repo

    Returns:
        Dictionary with keys: title, state, body, labels, linked_prs
    """
    from dev10x.mcp import github as gh

    return gh.issue_get(number=number, repo=repo)


@server.tool()
async def issue_comments(number: int, repo: str | None = None) -> dict:
    """Get GitHub issue comments.

    Args:
        number: Issue number
        repo: Repository (owner/repo). If omitted, uses current repo

    Returns:
        Dictionary with key: comments (list of comment objects)
    """
    from dev10x.mcp import github as gh

    return gh.issue_comments(number=number, repo=repo)


@server.tool()
async def issue_create(
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
    repo: str | None = None,
) -> dict:
    """Create a GitHub issue.

    Args:
        title: Issue title
        body: Issue body text (optional)
        labels: List of label names to apply (optional)
        repo: Repository (owner/repo). If omitted, uses current repo

    Returns:
        Dictionary with keys: number, title, url
    """
    from dev10x.mcp import github as gh

    return gh.issue_create(title=title, body=body, labels=labels, repo=repo)


@server.tool()
async def pr_comments(
    action: str,
    pr_number: int | None = None,
    comment_id: int | None = None,
    body: str | None = None,
    repo: str | None = None,
) -> dict:
    """Manage GitHub PR review comments and threads.

    Args:
        action: One of: list, get, reply, resolve
        pr_number: PR number (required for list, reply)
        comment_id: Comment ID (required for get, reply, resolve)
        body: Comment body text (required for reply)
        repo: Repository (owner/repo). If omitted, uses current repo

    Returns:
        Dictionary with action results (comments list or operation status)
    """
    from dev10x.mcp import github as gh

    return gh.pr_comments(
        action=action,
        pr_number=pr_number,
        comment_id=comment_id,
        body=body,
        repo=repo,
    )


@server.tool()
async def pr_comment_reply(
    pr_number: int,
    comment_id: int,
    body: str,
    repo: str | None = None,
) -> dict:
    """Reply to a PR review comment thread.

    Args:
        pr_number: PR number
        comment_id: Root comment ID to reply to
        body: Reply text (supports markdown)
        repo: Repository (owner/repo). If omitted, uses current repo

    Returns:
        Dictionary with reply details (id, body, created_at)
    """
    from dev10x.mcp import github as gh

    return gh.pr_comment_reply(
        pr_number=pr_number,
        comment_id=comment_id,
        body=body,
        repo=repo,
    )


@server.tool()
async def request_review(
    pr_number: int,
    reviewers: list[str],
    team: bool | None = None,
    repo: str | None = None,
) -> dict:
    """Request review on a GitHub PR from users or teams.

    Args:
        pr_number: PR number
        reviewers: List of reviewer usernames or team names
        team: Whether reviewers are teams (vs users)
        repo: Repository (owner/repo). If omitted, uses current repo

    Returns:
        Dictionary with keys: requested_reviewers or requested_teams
    """
    from dev10x.mcp import github as gh

    return gh.request_review(
        pr_number=pr_number,
        reviewers=reviewers,
        team=team,
        repo=repo,
    )


@server.tool()
async def detect_base_branch(base: str | None = None, force: bool = False) -> dict:
    """Detect the correct base branch for PRs in the current repository.

    Prefers develop/development, falls back to main/master/trunk.

    Args:
        base: Explicit base branch override
        force: Skip warning when overriding to non-development base

    Returns:
        Dictionary with keys: base_branch (str), has_develop (bool)
    """
    from dev10x.mcp import github as gh

    return gh.detect_base_branch(base=base, force=force)


@server.tool()
async def verify_pr_state(force: bool = False) -> dict:
    """Verify branch state before creating a PR.

    Args:
        force: Allow targeting a non-development base branch

    Returns:
        Dictionary with keys: branch_name, issue, base_branch
    """
    from dev10x.mcp import github as gh

    return gh.verify_pr_state(force=force)


@server.tool()
async def pre_pr_checks(base_branch: str | None = None) -> dict:
    """Run pre-PR quality checks (ruff, mypy, pytest).

    Args:
        base_branch: Base branch for diff comparison. Auto-detected if omitted.

    Returns:
        Dictionary with keys: success (bool), output (str)
    """
    from dev10x.mcp import github as gh

    return gh.pre_pr_checks(base_branch=base_branch)


@server.tool()
async def create_pr(
    title: str,
    job_story: str,
    issue_id: str,
    fixes_url: str | None = None,
    base_branch: str | None = None,
) -> dict:
    """Create a draft PR with two-pass body generation.

    Args:
        title: PR title
        job_story: JTBD Job Story for the PR body
        issue_id: Ticket ID extracted from branch name
        fixes_url: Issue URL for the Fixes: line
        base_branch: Base branch. Auto-detected if omitted.

    Returns:
        Dictionary with keys: pr_number (int), url (str)
    """
    from dev10x.mcp import github as gh

    return gh.create_pr(
        title=title,
        job_story=job_story,
        issue_id=issue_id,
        fixes_url=fixes_url,
        base_branch=base_branch,
    )


@server.tool()
async def generate_commit_list(pr_number: int, base_branch: str | None = None) -> dict:
    """Generate a linked commit list for a PR body.

    Args:
        pr_number: PR number for commit links
        base_branch: Base branch. Auto-detected if omitted.

    Returns:
        Dictionary with key: commit_list (str)
    """
    from dev10x.mcp import github as gh

    return gh.generate_commit_list(pr_number=pr_number, base_branch=base_branch)


@server.tool()
async def post_summary_comment(issue_id: str, summary_text: str) -> dict:
    """Post summary + checklist as first PR comment.

    Args:
        issue_id: Ticket ID for checklist substitution
        summary_text: Markdown bullet points (one per line)

    Returns:
        Dictionary with keys: success (bool), output (str)
    """
    from dev10x.mcp import github as gh

    return gh.post_summary_comment(issue_id=issue_id, summary_text=summary_text)


@server.tool()
async def pr_notify(
    pr_number: int,
    repo: str,
    action: str = "prepare",
    channel: str | None = None,
    message: str | None = None,
    message_file: str | None = None,
    reviewer: str | None = None,
    skip_slack: bool = False,
    skip_reviewers: bool = False,
    skip_checklist: bool = False,
) -> dict:
    """PR notification helper for review requests.

    Args:
        pr_number: PR number
        repo: GitHub repo (owner/name)
        action: "prepare" or "send"
        channel: Slack channel ID (send only)
        message: Notification message text (send only)
        message_file: Path to message file (send only)
        reviewer: GitHub reviewer to assign (send only)
        skip_slack: Skip Slack notification (send only)
        skip_reviewers: Skip reviewer assignment (send only)
        skip_checklist: Skip checklist update (send only)

    Returns:
        Dictionary with PR info (prepare) or operation results (send)
    """
    from dev10x.mcp import github as gh

    return gh.pr_notify(
        pr_number=pr_number,
        repo=repo,
        action=action,
        channel=channel,
        message=message,
        message_file=message_file,
        reviewer=reviewer,
        skip_slack=skip_slack,
        skip_reviewers=skip_reviewers,
        skip_checklist=skip_checklist,
    )


# ── Git tools ───────────────────────────────────────────────────


@server.tool()
async def push_safe(args: list[str], protected_branches: list[str] | None = None) -> dict:
    """Safely push git branches with protection for main/develop.

    Args:
        args: Arguments to pass to git push (e.g., ["origin", "branch-name"])
        protected_branches: List of branch names to protect (default: main, develop)

    Returns:
        Dictionary with keys: success (bool), branch, remote, blocked_reason (if blocked)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.push_safe(args=args, protected_branches=protected_branches)


@server.tool()
async def rebase_groom(seq_path: str, base_ref: str) -> dict:
    """Rebase and groom commits using an interactive sequence file.

    Args:
        seq_path: Path to git rebase sequence file
        base_ref: Base ref to rebase onto (e.g., develop, main)

    Returns:
        Dictionary with keys: success (bool), commits_rewritten (int)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.rebase_groom(seq_path=seq_path, base_ref=base_ref)


@server.tool()
async def create_worktree(
    branch: str,
    base: str | None = None,
    path: str | None = None,
) -> dict:
    """Create a new git worktree.

    Args:
        branch: Branch name for the worktree
        base: Base ref to create from (default: develop)
        path: Worktree path (default: ../.worktrees/{project}-NN)

    Returns:
        Dictionary with keys: worktree_path, branch, created (bool)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.create_worktree(branch=branch, base=base, path=path)


@server.tool()
async def mass_rewrite(config_path: str) -> dict:
    """Rewrite multiple commit messages in one unattended rebase pass.

    Args:
        config_path: Path to JSON config file with rewrite instructions.

    Returns:
        Dictionary with keys: success (bool), output (str), error (str if failed)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.mass_rewrite(config_path=config_path)


@server.tool()
async def start_split_rebase(commit_hash: str, base_branch: str = "develop") -> dict:
    """Start an interactive rebase to split a commit.

    Args:
        commit_hash: The commit hash to split
        base_branch: Base branch for the rebase (default: develop)

    Returns:
        Dictionary with keys: success (bool), output (str), error (str if failed)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.start_split_rebase(commit_hash=commit_hash, base_branch=base_branch)


@server.tool()
async def next_worktree_name(base_dir: str | None = None) -> dict:
    """Calculate the next available worktree path.

    Args:
        base_dir: Override worktrees parent directory (default: ../.worktrees)

    Returns:
        Dictionary with keys: path (str)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.next_worktree_name(base_dir=base_dir)


@server.tool()
async def setup_aliases() -> dict:
    """Set up global git aliases for branch comparison operations.

    Returns:
        Dictionary with keys: success (bool), output (str)
    """
    from dev10x.mcp import git as git_tools

    return git_tools.setup_aliases()


# ── Utility tools ───────────────────────────────────────────────


@server.tool()
async def mktmp(
    namespace: str,
    prefix: str,
    ext: str = "",
    directory: bool = False,
) -> dict:
    """Create a unique temp file or directory under /tmp/claude/<namespace>/.

    Args:
        namespace: Subdirectory under /tmp/claude/ (e.g., "git", "skill-audit")
        prefix: Filename prefix (e.g., "commit-msg", "pr-review")
        ext: File extension including dot (e.g., ".txt", ".json"). Ignored for directories.
        directory: If True, create a directory instead of a file.

    Returns:
        Dictionary with key: path (str) — the created temp file/directory path
    """
    from dev10x.mcp import utilities as util

    return util.mktmp(namespace=namespace, prefix=prefix, ext=ext, directory=directory)


def main() -> None:
    server.run()
