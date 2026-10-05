#!/usr/bin/env python3
# file: .github/scripts/monitor-rollout.py
# version: 1.1.2
# guid: 7f1a3b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c
# last-edited: 2026-10-05

"""Monitor rollout across target repositories.

- Reads target repos from .github/repositories.txt or TARGET_REPOS env (space/comma-separated)
- For each repo, fetches recent GitHub Actions runs and summarizes key workflows:
  - Security (security.yml)
  - Release (release.yml)
  - Sync Receiver (sync-receiver.yml)
- Writes a concise summary to stdout and to GITHUB_STEP_SUMMARY if available.

Optional flags:
  --per-page N       Number of recent runs to inspect per repo (default 10)
  --since-hours H    Only consider runs started within the last H hours (default 72)
  --repos "owner/repo ..."  Override repo list

Auth:
  - Uses JF_CI_GH_PAT or GITHUB_TOKEN from environment
"""

import argparse
import datetime as dt
import json
import os
import sys
from urllib import error, request

API_BASE = os.environ.get("GITHUB_API_URL", "https://api.github.com")
HTTP_OK = 200


def get_token() -> str | None:
    """Return the GitHub token from JF_CI_GH_PAT or GITHUB_TOKEN, if set."""
    return os.environ.get("JF_CI_GH_PAT") or os.environ.get("GITHUB_TOKEN")


def gh_headers() -> dict[str, str]:
    """Build GitHub REST API request headers, with auth when a token is set."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ghcommon-monitor-rollout",
    }
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def http_get(url: str) -> tuple[int, dict]:
    """GET a GitHub API URL; return (status, decoded JSON or error dict)."""
    if not url.startswith(("https://", "http://")):
        return 0, {"error": f"refusing non-HTTP(S) URL: {url}"}
    # Scheme checked above, so S310's file:/custom-scheme concern is handled.
    req = request.Request(url, headers=gh_headers())  # noqa: S310
    try:
        with request.urlopen(req, timeout=30) as resp:  # noqa: S310
            status = resp.getcode()
            data = resp.read()
            try:
                return status, json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                return status, {}
    except error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8")
        except Exception:
            payload = ""
        return e.code, {"error": str(e), "payload": payload}
    except Exception as e:
        return 0, {"error": str(e)}


def now_utc() -> dt.datetime:
    """Return the current time as an aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


def parse_iso8601(s: str) -> dt.datetime | None:
    """Parse an ISO 8601 timestamp (trailing Z allowed); None if invalid."""
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def load_target_repos(explicit: str | None) -> list[str]:
    """Resolve target repos from --repos, TARGET_REPOS or repositories.txt."""
    if explicit:
        return [
            p.strip() for p in explicit.replace(",", " ").split() if p.strip()
        ]
    env_repos = os.environ.get("TARGET_REPOS")
    if env_repos:
        return [
            p.strip() for p in env_repos.replace(",", " ").split() if p.strip()
        ]
    # Fallback to repositories.txt
    repos_file = os.path.join(os.getcwd(), ".github", "repositories.txt")
    repos: list[str] = []
    if os.path.exists(repos_file):
        with open(repos_file, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                # Support "repo" shorthand by defaulting owner to jdfalk
                if "/" not in line:
                    repos.append(f"jdfalk/{line}")
                else:
                    repos.append(line)
    return repos


def list_recent_runs(repo: str, per_page: int) -> list[dict]:
    """Return the most recent workflow runs for a repo ([] on API error)."""
    url = f"{API_BASE}/repos/{repo}/actions/runs?per_page={per_page}"
    status, payload = http_get(url)
    if status != HTTP_OK:
        return []
    return payload.get("workflow_runs", []) or []


def pick_latest(
    runs: list[dict], name_contains: list[str], since_cutoff: dt.datetime
) -> dict | None:
    """Return the newest run whose name contains every term, since cutoff."""
    name_lc = [n.lower() for n in name_contains]
    for run in runs:
        n = (run.get("name") or "").lower()
        created_at = parse_iso8601(
            run.get("created_at") or run.get("run_started_at") or ""
        )
        if (
            all(term in n for term in name_lc)
            and created_at
            and created_at >= since_cutoff
        ):
            return run
    return None


def summarize_repo(repo: str, per_page: int, since_hours: int) -> dict:
    """Summarize the latest security, release and sync runs for a repo."""
    runs = list_recent_runs(repo, per_page)
    cutoff = now_utc() - dt.timedelta(hours=since_hours)
    sec = pick_latest(runs, ["security"], cutoff)
    rel = pick_latest(runs, ["release"], cutoff)
    # Match various names for the sync receiver workflow
    sync = pick_latest(runs, ["sync", "receiver"], cutoff) or pick_latest(
        runs, ["repo", "sync"], cutoff
    )

    def status_of(run: dict | None) -> str:
        if not run:
            return "missing"
        # conclusion may be None while in progress
        return run.get("conclusion") or run.get("status") or "unknown"

    return {
        "repo": repo,
        "security": {
            "status": status_of(sec),
            "url": sec.get("html_url") if sec else None,
        },
        "release": {
            "status": status_of(rel),
            "url": rel.get("html_url") if rel else None,
        },
        "sync_receiver": {
            "status": status_of(sync),
            "url": sync.get("html_url") if sync else None,
        },
    }


def write_step_summary(md: str) -> None:
    """Write summary to both job summary and stdout for visibility."""
    # Always echo to logs for easy inspection
    print(md)

    # Also write to step summary panel if available
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(md)
    except Exception as e:
        print(f"Failed writing step summary: {e}", file=sys.stderr)


def build_markdown(results: list[dict]) -> str:
    """Render the rollout results as a Markdown summary."""
    lines = ["# Rollout Verification Summary", ""]
    ok_all = True
    for r in results:
        repo = r["repo"]
        sec = r["security"]["status"]
        rel = r["release"]["status"]
        syn = r["sync_receiver"]["status"]

        def badge(st: str) -> str:
            if st in ("success", "completed"):
                return "✅"
            if st in ("in_progress", "queued", "waiting"):
                return "⏳"
            if st == "missing":
                return "⚪"
            return "❌"

        if sec not in ("success", "completed") or rel not in (
            "success",
            "completed",
        ):
            ok_all = False
        lines.append(f"## {repo}")
        lines.append(
            f"- Security: {badge(sec)} {sec}{' | ' + r['security']['url'] if r['security']['url'] else ''}"
        )
        lines.append(
            f"- Release: {badge(rel)} {rel}{' | ' + r['release']['url'] if r['release']['url'] else ''}"
        )
        lines.append(
            f"- Sync Receiver: {badge(syn)} {syn}{' | ' + r['sync_receiver']['url'] if r['sync_receiver']['url'] else ''}"
        )
        lines.append("")
    overall = "All green" if ok_all else "Attention needed"
    lines.insert(1, f"Overall: {overall}")
    lines.insert(2, "")
    return "\n".join(lines)


def main() -> int:
    """Summarize rollout status for every target repo; return the exit code."""
    parser = argparse.ArgumentParser(
        description="Monitor rollout across target repositories"
    )
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument("--since-hours", type=int, default=72)
    parser.add_argument("--repos", type=str, default="")
    args = parser.parse_args()

    repos = load_target_repos(args.repos)
    if not repos:
        print("No target repositories found.")
        return 1
    if not get_token():
        print(
            "Warning: No token provided (JF_CI_GH_PAT/GITHUB_TOKEN). You may hit rate limits."
        )

    results: list[dict] = []
    for repo in repos:
        try:
            results.append(
                summarize_repo(repo, args.per_page, args.since_hours)
            )
        except Exception as e:
            results.append(
                {
                    "repo": repo,
                    "security": {"status": f"error: {e}", "url": None},
                    "release": {"status": "unknown", "url": None},
                    "sync_receiver": {"status": "unknown", "url": None},
                }
            )

    md = build_markdown(results)
    write_step_summary(md)

    # Also write an overall status to GITHUB_OUTPUT
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        try:
            # Consider both security and release statuses for overall health
            def ok_status(st: str) -> bool:
                return st in ("success", "completed")

            all_ok = all(
                ok_status(r["security"]["status"])
                and ok_status(r["release"]["status"])  # type: ignore[index]
                for r in results
            )
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"overall={'green' if all_ok else 'needs_attention'}\n")
        except Exception as e:
            print(
                f"::warning::could not write overall status to GITHUB_OUTPUT: {e}",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
