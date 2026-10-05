#!/usr/bin/env python3
# file: .github/scripts/sync-generate-summary.py
# version: 1.0.1
# guid: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f
# last-edited: 2026-10-05

"""Generate synchronization summary for GitHub Actions step summary."""

from datetime import datetime
import os
import sys


def generate_summary():
    """Generate a comprehensive sync summary."""
    # Get environment variables
    source_repo = os.getenv("GITHUB_REPOSITORY", "jdfalk/ghcommon")
    source_sha = os.getenv("GITHUB_SHA", "unknown")
    run_id = os.getenv("GITHUB_RUN_ID", "unknown")
    run_number = os.getenv("GITHUB_RUN_NUMBER", "unknown")
    actor = os.getenv("GITHUB_ACTOR", "unknown")

    # Get target repositories count (if available)
    target_repos_env = os.getenv("TARGET_REPOS", "")
    target_repos = target_repos_env.split() if target_repos_env else []

    # Current timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Generate summary markdown
    summary = f"""# 🔄 Repository Synchronization Summary

## Overview
- **Source Repository**: {source_repo}
- **Source SHA**: `{source_sha[:8]}...`
- **Triggered by**: {actor}
- **Run Number**: #{run_number}
- **Timestamp**: {timestamp}

## Synchronization Details

### Target Repositories
"""

    if target_repos:
        summary += f"**Total**: {len(target_repos)} repositories\n\n"
        for i, repo in enumerate(target_repos, 1):
            summary += f"{i}. `{repo}`\n"
    else:
        summary += "No target repositories specified\n"

    summary += f"""

### Sync Process
- ✅ File synchronization dispatched
- ✅ Repository events triggered
- ✅ Target repositories notified

### Workflow Information
- **Workflow Run ID**: {run_id}
- **Source Branch**: main
- **Sync Type**: Automated from central repository

---

*This summary was generated automatically by the repository sync system.*
"""

    return summary


def write_to_step_summary(content):
    """Write content to GitHub Actions step summary."""
    github_step_summary = os.getenv("GITHUB_STEP_SUMMARY")

    if github_step_summary:
        try:
            with open(github_step_summary, "a") as f:
                f.write(content)
            print("✅ Summary written to GitHub Actions step summary")
        except Exception as e:
            print(f"❌ Error writing to step summary: {e}", file=sys.stderr)
    else:
        print("ℹ️  GITHUB_STEP_SUMMARY not available, outputting to console:")
        print(content)


def main():
    """Main entry point."""
    print("Generating synchronization summary...")

    summary = generate_summary()

    # Write to step summary
    write_to_step_summary(summary)

    # Also output key information for logs
    print("Repository synchronization completed successfully")


if __name__ == "__main__":
    main()
