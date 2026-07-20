#!/usr/bin/env python3
# file: scripts/intelligent_sync_to_repos.py
# version: 1.5.0
# guid: a1b2c3d4-e5f6-7890-1234-567890abcdef

"""Intelligent sync script that understands the new modular .github structure.

This script:
1. Syncs the new modular structure (.github/instructions/, .github/prompts/, .github/agents/)
2. Cleans up old files that have been moved/restructured
3. Preserves repo-specific files
4. Creates proper VS Code symlinks for Copilot integration
5. Automatically creates PRs for review and merge
6. Closes superseded PRs from previous sync attempts
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Files managed by ghcommon that should be synced
MANAGED_FILES = {
    # Core instruction system
    ".github/copilot-instructions.md",
    ".github/instructions/general-coding.instructions.md",
    ".github/instructions/github-actions.instructions.md",
    ".github/instructions/go.instructions.md",
    ".github/instructions/html-css.instructions.md",
    ".github/instructions/javascript.instructions.md",
    ".github/instructions/json.instructions.md",
    ".github/instructions/markdown.instructions.md",
    ".github/instructions/protobuf.instructions.md",
    ".github/instructions/python.instructions.md",
    ".github/instructions/r.instructions.md",
    ".github/instructions/shell.instructions.md",
    ".github/instructions/typescript.instructions.md",
    ".github/instructions/commit-messages.instructions.md",
    ".github/instructions/pull-request-descriptions.instructions.md",
    # Agent files for GitHub Copilot
    ".github/agents/CI Workflow Doctor.agent.md",
    ".github/agents/Cross-Repo Sync Manager.agent.md",
    ".github/agents/Dependency Auditor.agent.md",
    ".github/agents/Documentation Curator.agent.md",
    ".github/agents/Git Hygiene Guardian.agent.md",
    ".github/agents/Go Static Analyzer.agent.md",
    ".github/agents/Lint & Format Conductor.agent.md",
    ".github/agents/Migration Planner.agent.md",
    ".github/agents/Performance Micro-Bencher.agent.md",
    ".github/agents/Protobuf Builder.agent.md",
    ".github/agents/Protobuf Cycle Resolver.agent.md",
    ".github/agents/Python Static Analyzer.agent.md",
    ".github/agents/Release & Version Steward.agent.md",
    ".github/agents/Rust Static Analyzer.agent.md",
    ".github/agents/Security Scanner Coordinator.agent.md",
    ".github/agents/Shell Workflow Assistant.agent.md",
    ".github/agents/Test Orchestrator.agent.md",
    ".github/agents/merge-conflict-resolution.agent.md",
    # Linter configurations (for GitHub Actions workflows)
    ".github/linters/.eslintrc.json",
    ".github/linters/.markdownlint.json",
    ".github/linters/.pylintrc",
    ".github/linters/.python-black",
    ".github/linters/.stylelintrc.json",
    ".github/linters/.yaml-lint.yml",
    ".github/linters/README.md",
    ".github/linters/ruff.toml",
    # Prompts
    ".github/prompts/ai-architecture.prompt.md",
    ".github/prompts/ai-changelog.prompt.md",
    ".github/prompts/ai-contribution.prompt.md",
    ".github/prompts/ai-issue-triage.prompt.md",
    ".github/prompts/ai-migration.prompt.md",
    ".github/prompts/ai-rebase-system.prompt.md",
    ".github/prompts/ai-refactor.prompt.md",
    ".github/prompts/ai-release-notes.prompt.md",
    ".github/prompts/ai-roadmap.prompt.md",
    ".github/prompts/bug-report.prompt.md",
    ".github/prompts/code-review.prompt.md",
    ".github/prompts/commit-message.prompt.md",
    ".github/prompts/documentation.prompt.md",
    ".github/prompts/feature-request.prompt.md",
    ".github/prompts/onboarding.prompt.md",
    ".github/prompts/pull-request.prompt.md",
    ".github/prompts/security-review.prompt.md",
    ".github/prompts/test-generation.prompt.md",
    # Changelog fragments (scriv) scaffolding. CHANGELOG.md is assembled from
    # these fragments by the reusable release workflow and enforced by the
    # reusable CI workflow; both are opt-in by presence of changelog.d/scriv.ini.
    # CHANGELOG.md itself is repo-specific and intentionally NOT synced.
    "changelog.d/scriv.ini",
    "changelog.d/templates/new_fragment.md.j2",
    "changelog.d/README.md",
    # TODO fragment scaffolding. TODO.md is assembled from these fragments by
    # scripts/assemble_todo.py, run by .github/workflows/todo-collect.yml;
    # opt-in by presence of todo.d/todo.ini. TODO.md itself is repo-specific
    # and intentionally NOT synced — it carries each repo's own insert marker.
    "todo.d/todo.ini",
    "todo.d/templates/new_fragment.md",
    "todo.d/README.md",
    "scripts/assemble_todo.py",
    ".github/workflows/todo-collect.yml",
    # Core documentation (versioned) - DEPRECATED, moved to instructions/
    # These are kept for backward compatibility but should be removed eventually
    ".github/test-generation.md",
    # Pointer files in root
    "AGENTS.md",
    "CLAUDE.md",
}

# Old files that should be cleaned up (moved to new structure)
OLD_FILES_TO_REMOVE = {
    # These have been moved to .github/instructions/
    ".github/code-style-general.md",
    ".github/code-style-go.md",
    ".github/code-style-python.md",
    ".github/code-style-javascript.md",
    ".github/code-style-typescript.md",
    ".github/code-style-markdown.md",
    ".github/code-style-json.md",
    ".github/code-style-shell.md",
    ".github/code-style-html-css.md",
    ".github/code-style-protobuf.md",
    ".github/code-style-r.md",
    ".github/code-style-github-actions.md",
    # Redundant files (moved to instructions/)
    ".github/commit-messages.md",
    ".github/pull-request-descriptions.md",
}

# Repo-specific files that should NOT be overwritten
REPO_SPECIFIC_FILES = {
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/",
    ".github/labeler.yml",  # May have repo-specific rules
    ".github/workflows/",  # May have repo-specific workflows
}


def parse_args():
    """Parse the command-line arguments for a sync run."""
    parser = argparse.ArgumentParser(
        description="Intelligently sync .github structure to target repos."
    )
    parser.add_argument(
        "--repos", required=True, help="Comma-separated list of target repos"
    )
    parser.add_argument(
        "--branch", required=True, help="Branch name to push to"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    return parser.parse_args()


def run(cmd: list[str], cwd=None, check=True, dry_run=False):
    """Run a command, logging it first and honoring dry-run mode."""
    logging.info(f"$ {' '.join(cmd)}")
    if dry_run:
        logging.info("  [DRY RUN] Command not executed")
        return None
    result = subprocess.run(
        cmd, cwd=cwd, check=check, capture_output=True, text=True
    )
    if result.stdout:
        logging.info(result.stdout)
    if result.stderr:
        logging.error(result.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )
    return result


def create_vscode_copilot_symlinks(repo_dir: str, dry_run: bool):
    """Create .vscode/copilot symlinks pointing at .github/instructions."""
    vscode_copilot_dir = os.path.join(repo_dir, ".vscode", "copilot")
    github_instructions_dir = os.path.join(repo_dir, ".github", "instructions")

    if not os.path.exists(github_instructions_dir):
        logging.info(
            "  [SKIP] .github/instructions/ not found, skipping VS Code symlinks"
        )
        return

    if dry_run:
        logging.info("  [DRY RUN] Would create .vscode/copilot/ symlinks")
        return

    os.makedirs(vscode_copilot_dir, exist_ok=True)

    # Create symlinks for all instruction files
    for file in os.listdir(github_instructions_dir):
        if file.endswith(".instructions.md"):
            src = os.path.join("..", "..", ".github", "instructions", file)
            dst = os.path.join(vscode_copilot_dir, file)

            # Remove existing file/symlink
            if os.path.exists(dst) or os.path.islink(dst):
                os.remove(dst)

            os.symlink(src, dst)
            logging.info(
                f"  Created symlink: .vscode/copilot/{file} -> ../../.github/instructions/{file}"
            )


def sync_to_repo(
    repo: str, branch: str, gh_token: str, summary: list[str], dry_run: bool
):
    """Sync the managed files into one repo and open or update its PR."""
    logging.info(f"\n=== Syncing to {repo} ===")

    if dry_run:
        # Show detailed dry-run preview
        logging.info("  DRY RUN - Would make these changes:")

        # Check what old files would be removed
        for old_file in OLD_FILES_TO_REMOVE:
            logging.info(f"    REMOVE: {old_file} (if exists)")

        # Check what managed files would be synced
        for managed_file in MANAGED_FILES:
            src = os.path.abspath(managed_file)
            if os.path.exists(src):
                logging.info(f"    SYNC: {managed_file}")
            else:
                logging.info(f"    SKIP: {managed_file} (source not found)")

        # Show VS Code symlinks that would be created
        logging.info("    VS Code Copilot symlinks:")
        for file in MANAGED_FILES:
            if file.startswith(".github/instructions/") and file.endswith(
                ".instructions.md"
            ):
                basename = os.path.basename(file)
                logging.info(
                    f"      CREATE: .vscode/copilot/{basename} -> ../../{file}"
                )

        summary.append(
            f"[DRY RUN] {repo}: Would sync {len(MANAGED_FILES)} files and clean up {len(OLD_FILES_TO_REMOVE)} old files"
        )
        return

    # Use GitHub token in URL for authentication
    repo_url = f"https://x-oauth-basic:{gh_token}@github.com/{repo}.git"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone the target repo
        run(["git", "clone", "--depth=1", repo_url, tmpdir], dry_run=dry_run)

        # Configure git credentials for push
        run(
            ["git", "config", "credential.helper", "store"],
            cwd=tmpdir,
            dry_run=dry_run,
        )
        run(
            ["git", "config", "user.name", "ghcommon-sync-bot"],
            cwd=tmpdir,
            dry_run=dry_run,
        )
        run(
            [
                "git",
                "config",
                "user.email",
                "ghcommon-sync-bot@users.noreply.github.com",
            ],
            cwd=tmpdir,
            dry_run=dry_run,
        )

        # Create/checkout branch
        result = run(
            ["git", "checkout", branch],
            cwd=tmpdir,
            check=False,
            dry_run=dry_run,
        )
        if result and result.returncode != 0:
            run(["git", "checkout", "-b", branch], cwd=tmpdir, dry_run=dry_run)

        changes_made = False

        # 1. Remove old files that have been moved
        for old_file in OLD_FILES_TO_REMOVE:
            old_path = os.path.join(tmpdir, old_file)
            if os.path.exists(old_path):
                logging.info(f"  Removing old file: {old_file}")
                if os.path.isdir(old_path):
                    shutil.rmtree(old_path)
                else:
                    os.remove(old_path)
                changes_made = True

        # 2. Sync managed files from ghcommon
        for managed_file in MANAGED_FILES:
            src = os.path.abspath(managed_file)
            dst = os.path.join(tmpdir, managed_file)

            if not os.path.exists(src):
                logging.info(f"  [WARN] Source file not found: {managed_file}")
                continue

            # Create directory if needed
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Copy file
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

            logging.info(f"  Synced: {managed_file}")
            changes_made = True

        # 3. Create VS Code Copilot symlinks
        create_vscode_copilot_symlinks(tmpdir, dry_run)
        changes_made = True

        # 4. Commit and push changes
        if changes_made:
            run(["git", "add", "."], cwd=tmpdir, dry_run=dry_run)

            commit_msg = """chore(sync): sync .github structure from ghcommon

- Updated to new modular instruction system
- Synced .github/instructions/ and .github/prompts/
- Removed old code-style-*.md files (moved to instructions/)
- Created VS Code Copilot symlinks for instruction files

This maintains the centralized coding standards while supporting
the new VS Code Copilot customization features."""

            try:
                run(
                    ["git", "commit", "-m", commit_msg],
                    cwd=tmpdir,
                    dry_run=dry_run,
                )
            except subprocess.CalledProcessError:
                summary.append(f"[SKIP] {repo}: No changes to commit")
                return

            try:
                run(
                    ["git", "push", "-u", "origin", branch, "--force"],
                    cwd=tmpdir,
                    dry_run=dry_run,
                )
                summary.append(f"[OK] {repo}: Synced to branch {branch}")

                # Create or update PR after successful sync
                if not dry_run:
                    create_or_update_pr(
                        repo, branch, summary
                    )  # PR creation handled separately
            except subprocess.CalledProcessError as e:
                summary.append(f"[FAIL] {repo}: Push failed - {e!s}")
        else:
            summary.append(f"[SKIP] {repo}: No changes needed")


def create_or_update_pr(repo, branch, summary):
    """Create a PR for the synced changes or update existing one.

    Also closes any superseded PRs from previous sync attempts.
    """
    # Close any existing open PRs for sync branches (superseded ones)
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--json",
                "number,headRefName,title",
                "-q",
                '.[] | select(.headRefName | startswith("chore/sync") or startswith("feature/sync")) | .number',
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        existing_prs = [int(x) for x in result.stdout.strip().split("\n") if x]

        for pr_num in existing_prs:
            logging.info(f"  Closing superseded PR #{pr_num}")
            subprocess.run(
                [
                    "gh",
                    "pr",
                    "close",
                    str(pr_num),
                    "--repo",
                    repo,
                    "--delete-branch",
                ],
                check=True,
                capture_output=True,
            )
    except subprocess.CalledProcessError as e:
        logging.warning(f"Could not close existing PRs: {e}")

    # Create new PR with retry logic (GitHub may need time to replicate the branch)
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logging.info(f"  Retry attempt {attempt}/{max_retries - 1}")
                time.sleep(retry_delay)

            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--repo",
                    repo,
                    "--base",
                    "main",
                    "--head",
                    branch,
                    "--title",
                    "chore(sync): sync .github structure from ghcommon",
                    "--body",
                    """## Overview
Automated sync of centralized .github configuration from [jdfalk/ghcommon](https://github.com/jdfalk/ghcommon).

## Changes
- Updated instruction files from `.github/instructions/`
- Synced prompt files from `.github/prompts/`
- Added GitHub Copilot agents from `.github/agents/`
- Created VS Code Copilot symlinks for proper integration
- Removed deprecated code-style files

## Review & Merge
This PR is ready for immediate approval and merge once CI passes.
The sync process is automated and this PR represents the latest state of the centralized configuration.

## Related
See [jdfalk/ghcommon](https://github.com/jdfalk/ghcommon) for the source of truth.""",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            pr_url = result.stdout.strip()
            summary.append(f"[PR] {repo}: Created PR at {pr_url}")
            logging.info(f"  Created PR: {pr_url}")
            break  # Success, exit retry loop
        except subprocess.CalledProcessError as e:
            if attempt == max_retries - 1:
                # Last attempt failed, log the error
                logging.warning(
                    f"Could not create PR for {repo} after {max_retries} attempts: {e.stderr}"
                )
                summary.append(
                    f"[WARN] {repo}: Could not create PR - {e.stderr.strip()}"
                )
            else:
                logging.info(
                    f"  PR creation failed, waiting {retry_delay}s before retry..."
                )


def main():
    """Sync every requested repo and write a run summary."""
    args = parse_args()

    if not args.dry_run:
        gh_token = os.environ.get("GH_TOKEN")
        if not gh_token:
            print("GH_TOKEN environment variable is required.", file=sys.stderr)
            sys.exit(1)
    else:
        gh_token = "dummy-for-dry-run"  # noqa: S105 - placeholder, never used to authenticate

    repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    branch = args.branch
    summary = []

    logging.info(f"Syncing to {len(repos)} repositories:")
    for repo in repos:
        logging.info(f"  - {repo}")

    logging.info(f"\nManaged files to sync: {len(MANAGED_FILES)}")
    logging.info(f"Old files to clean up: {len(OLD_FILES_TO_REMOVE)}")

    if args.dry_run:
        logging.info("\n*** DRY RUN MODE - No changes will be made ***\n")

    for repo in repos:
        try:
            sync_to_repo(repo, branch, gh_token, summary, args.dry_run)
        except Exception as e:
            summary.append(f"[FAIL] {repo}: {e!s}")
            logging.error(f"Failed to sync {repo}: {e}")

    # Write summary
    summary_file = "intelligent-sync-summary.log"
    with open(summary_file, "w") as f:
        for line in summary:
            f.write(line + "\n")

    logging.info("\n=== SYNC SUMMARY ===")
    for line in summary:
        logging.info(line)


if __name__ == "__main__":
    main()
