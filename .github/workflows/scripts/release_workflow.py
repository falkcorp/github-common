#!/usr/bin/env python3
# file: .github/workflows/scripts/release_workflow.py
# version: 2.2.0
# guid: dc14e86d-ff9a-4317-88de-23e0e48651d2
# last-edited: 2026-10-16
"""Helper utilities for reusable release workflows."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess

import requests
from workflow_common import (
    append_to_file,
    config_path,
    write_output,
)


def _normalize_override(value: str | None) -> str:
    if value is None:
        return "auto"
    value = value.lower()
    if value in {"true", "false"}:
        return value
    return "auto"


def _build_target_set(build_target: str) -> set[str]:
    if not build_target or build_target == "all":
        return {"go", "python", "rust", "frontend", "docker", "protobuf"}
    return {
        entry.strip().lower()
        for entry in build_target.split(",")
        if entry.strip()
    }


def _derive_flag(
    override: str, key: str, targets: set[str], default: bool
) -> bool:
    if override == "true":
        return True
    if override == "false":
        return False
    if "all" in targets:
        return True
    if not targets:
        return default
    return key in targets or default


def _any_proto_files(limit: int = 20) -> bool:
    count = 0
    for _ in Path(".").rglob("*.proto"):
        count += 1
        if count >= limit:
            return True
    return count > 0


def _matrix_json(
    version_key: str, versions: Iterable[str], oses: Iterable[str]
) -> str:
    matrix = {
        version_key: list(dict.fromkeys(versions)),
        "os": list(dict.fromkeys(oses)),
    }
    return json.dumps(matrix, separators=(",", ":"))


def _docker_matrix_json(platforms: Iterable[str]) -> str:
    matrix = {"platform": list(dict.fromkeys(platforms))}
    return json.dumps(matrix, separators=(",", ":"))


def detect_languages(_: argparse.Namespace) -> None:
    skip_detection = (
        os.environ.get("SKIP_LANGUAGE_DETECTION", "false").lower() == "true"
    )
    targets = _build_target_set(os.environ.get("BUILD_TARGET", "all").lower())

    overrides = {
        "go": _normalize_override(os.environ.get("GO_ENABLED")),
        "python": _normalize_override(os.environ.get("PYTHON_ENABLED")),
        "rust": _normalize_override(os.environ.get("RUST_ENABLED")),
        "frontend": _normalize_override(os.environ.get("FRONTEND_ENABLED")),
        "docker": _normalize_override(os.environ.get("DOCKER_ENABLED")),
        "protobuf": _normalize_override(os.environ.get("PROTOBUF_ENABLED")),
    }

    if skip_detection:
        has_go = _derive_flag(overrides["go"], "go", targets, False)
        has_python = _derive_flag(overrides["python"], "python", targets, False)
        has_rust = _derive_flag(overrides["rust"], "rust", targets, False)
        has_frontend = _derive_flag(
            overrides["frontend"], "frontend", targets, False
        )
        has_docker = _derive_flag(overrides["docker"], "docker", targets, False)
        protobuf_needed = _derive_flag(
            overrides["protobuf"], "protobuf", targets, False
        )
    else:
        has_go = (
            Path("go.mod").is_file()
            or Path("main.go").is_file()
            or Path("cmd").exists()
            or Path("pkg").exists()
        )
        has_python = any(
            Path(".").joinpath(name).exists()
            for name in [
                "setup.py",
                "pyproject.toml",
                "requirements.txt",
                "poetry.lock",
            ]
        )
        has_rust = Path("Cargo.toml").is_file() or Path("Cargo.lock").is_file()
        has_frontend = (
            Path("package.json").is_file()
            or Path("webui").exists()
            or Path("frontend").exists()
            or Path("ui").exists()
        )
        has_docker = (
            any(Path(".").glob("Dockerfile*"))
            or Path("docker-compose.yml").is_file()
            or Path("docker-compose.yaml").is_file()
        )
        protobuf_needed = (
            Path("buf.yaml").is_file()
            or Path("buf.gen.yaml").is_file()
            or _any_proto_files()
        )

        for key, override in overrides.items():
            if override == "true":
                if key == "go":
                    has_go = True
                elif key == "python":
                    has_python = True
                elif key == "rust":
                    has_rust = True
                elif key == "frontend":
                    has_frontend = True
                elif key == "docker":
                    has_docker = True
                elif key == "protobuf":
                    protobuf_needed = True
            elif override == "false":
                if key == "go":
                    has_go = False
                elif key == "python":
                    has_python = False
                elif key == "rust":
                    has_rust = False
                elif key == "frontend":
                    has_frontend = False
                elif key == "docker":
                    has_docker = False
                elif key == "protobuf":
                    protobuf_needed = False

    config_primary = config_path("auto", "repository", "primary_language")
    if config_primary and config_primary != "auto":
        primary_language = str(config_primary)
    else:
        primary_language = "multi"
        for candidate, flag in (
            ("rust", has_rust),
            ("go", has_go),
            ("python", has_python),
            ("frontend", has_frontend),
            ("docker", has_docker),
        ):
            if flag:
                primary_language = candidate
                break

    write_output("has-go", "true" if has_go else "false")
    write_output("has-python", "true" if has_python else "false")
    write_output("has-rust", "true" if has_rust else "false")
    write_output("has-frontend", "true" if has_frontend else "false")
    write_output("has-docker", "true" if has_docker else "false")
    write_output("protobuf-needed", "true" if protobuf_needed else "false")
    write_output("primary-language", primary_language)

    versions = config_path({}, "languages", "versions") or {}
    platforms = config_path({}, "build", "platforms") or {}
    os_list = platforms.get("os") or ["ubuntu-latest", "macos-latest"]
    go_versions = versions.get("go") or ["1.22", "1.23", "1.24"]
    python_versions = versions.get("python") or ["3.11", "3.12", "3.13"]
    rust_versions = versions.get("rust") or ["stable", "beta"]
    node_versions = versions.get("node") or ["18", "20", "22"]
    docker_platforms = config_path(
        ["linux/amd64", "linux/arm64"], "build", "docker", "platforms"
    )

    write_output("go-matrix", _matrix_json("go-version", go_versions, os_list))
    write_output(
        "python-matrix",
        _matrix_json("python-version", python_versions, os_list),
    )
    write_output(
        "rust-matrix", _matrix_json("rust-version", rust_versions, os_list)
    )
    write_output(
        "frontend-matrix",
        _matrix_json("node-version", node_versions, ["ubuntu-latest"]),
    )
    write_output("docker-matrix", _docker_matrix_json(docker_platforms))


def release_strategy(_: argparse.Namespace) -> None:
    branch = os.environ.get("BRANCH_NAME", "")
    input_prerelease = (
        os.environ.get("INPUT_PRERELEASE", "false").lower() == "true"
    )
    input_draft = os.environ.get("INPUT_DRAFT", "false").lower() == "true"

    if branch == "main":
        strategy = "stable"
        auto_prerelease = False
        auto_draft = True
    else:
        strategy = "prerelease"
        auto_prerelease = True
        auto_draft = False

    if input_prerelease:
        auto_prerelease = True
    if input_draft:
        auto_draft = True

    write_output("strategy", strategy)
    write_output("auto-prerelease", "true" if auto_prerelease else "false")
    write_output("auto-draft", "true" if auto_draft else "false")

    print(f"🔄 Release strategy for branch '{branch}': {strategy}")
    print(f"📋 Auto-prerelease: {auto_prerelease}")
    print(f"📋 Auto-draft: {auto_draft}")


def _run_git(
    args: list[str], check: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args, check=check, capture_output=True, text=True
    )


def _latest_tag_from_api() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        return ""

    url = f"https://api.github.com/repos/{repository}/releases/latest"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException:
        return ""

    if response.status_code != 200:
        return ""

    try:
        data = response.json()
    except ValueError:
        return ""

    tag = data.get("tag_name")
    if tag and isinstance(tag, str):
        return tag
    return ""


def _latest_tag_from_git() -> str:
    result = _run_git(["tag", "-l", "--sort=-version:refname"])
    for line in result.stdout.splitlines():
        candidate = line.strip()
        if re.match(r"^v\d+\.\d+\.\d+", candidate):
            return candidate

    describe = _run_git(["describe", "--tags", "--abbrev=0"])
    if describe.returncode == 0 and describe.stdout.strip():
        return describe.stdout.strip()

    return "v0.0.0"


def generate_version(_: argparse.Namespace) -> None:
    release_type = os.environ.get("RELEASE_TYPE", "auto").lower()
    branch_name = os.environ.get("BRANCH_NAME", "")
    auto_prerelease = (
        os.environ.get("AUTO_PRERELEASE", "false").lower() == "true"
    )

    print("🔍 Detecting latest version...")
    latest_tag = _latest_tag_from_api()
    if latest_tag:
        print(f"✅ Found latest release via API: {latest_tag}")
    else:
        print("⚠️ No releases found via API, using git tags...")
        latest_tag = _latest_tag_from_git()
        print(f"📌 Using base version: {latest_tag}")

    version_core = re.sub(r"^v", "", latest_tag).split("-")[0]
    parts = version_core.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    if release_type == "major":
        new_major, new_minor, new_patch = major + 1, 0, 0
    elif release_type == "minor":
        new_major, new_minor, new_patch = major, minor + 1, 0
    elif release_type == "patch" or branch_name == "main":
        new_major, new_minor, new_patch = major, minor, patch + 1
    elif branch_name == "develop":
        new_major, new_minor, new_patch = major, minor + 1, 0
    else:
        new_major, new_minor, new_patch = major, minor, patch + 1

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
    if auto_prerelease:
        suffix = "dev" if branch_name == "develop" else "alpha"
        version_tag = (
            f"v{new_major}.{new_minor}.{new_patch}-{suffix}.{timestamp}"
        )
    else:
        version_tag = f"v{new_major}.{new_minor}.{new_patch}"

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    while True:
        existing = _run_git(["tag", "-l", version_tag])
        if not existing.stdout.strip():
            break

        print(f"⚠️ Tag {version_tag} already exists")
        if event_name == "workflow_dispatch":
            print("🔄 Manual release detected; deleting existing tag")
            _run_git(["tag", "-d", version_tag])
            token = os.environ.get("GITHUB_TOKEN")
            repository = os.environ.get("GITHUB_REPOSITORY")
            if token and repository:
                subprocess.run(
                    [
                        "git",
                        "push",
                        f"https://x-access-token:{token}@github.com/{repository}.git",
                        f":refs/tags/{version_tag}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            break

        if auto_prerelease:
            suffix = "dev" if branch_name == "develop" else "alpha"
            version_tag = f"v{new_major}.{new_minor}.{new_patch}-{suffix}.{timestamp}.{int(datetime.utcnow().timestamp())}"
        else:
            new_patch += 1
            version_tag = f"v{new_major}.{new_minor}.{new_patch}"
        if new_patch - patch > 10:
            version_tag = (
                f"v{new_major}.{new_minor}.{new_patch}-build.{timestamp}"
            )
            break

    print(f"✅ Final version tag: {version_tag}")
    write_output("tag", version_tag)


# GitHub rejects a release body over 125,000 characters. The release and
# draft steps add their own header/footer (~1.5 KB) around these notes, so
# the commit list gets a budget well under that.
CHANGELOG_COMMITS_BUDGET = 110_000


def _omitted_line(count: int, *, newest: bool = False) -> str:
    """Return the closing line that says how many commits were left out."""
    which = "" if newest else " older"
    return (
        f"- … and {count}{which} commit(s) not listed "
        "(release notes are capped at GitHub's body limit)"
    )


def _cap_commit_lines(commits: list[str], budget: int) -> list[str]:
    """Return "- commit" lines whose joined length fits budget characters.

    Commits are newest first, so the oldest are the ones dropped and a final
    line says how many were left out. The budget counts characters (what
    GitHub limits), including the newline between lines. A list that fits
    whole is returned unchanged. Otherwise a commit is kept only if the
    omitted-count line for everything after it still fits, so that line
    always has room when the list is cut. A budget smaller than that line
    itself (under ~90 characters) cannot be honoured; callers use 110,000.
    """
    lines = [f"- {commit}" for commit in commits]
    if len("\n".join(lines)) <= budget:
        return lines
    kept: list[str] = []
    used = 0
    for index, commit in enumerate(commits):
        line = f"- {commit}"
        after = len(commits) - index - 1
        need = len(line) + (1 if kept else 0)
        if after:
            need += 1 + len(_omitted_line(after))
        if used + need > budget:
            kept.append(_omitted_line(len(commits) - index, newest=not kept))
            return kept
        kept.append(line)
        used += len(line) + (1 if len(kept) > 1 else 0)
    return kept


def generate_changelog(_: argparse.Namespace) -> None:
    branch = os.environ.get("BRANCH_NAME", "")
    primary_language = os.environ.get("PRIMARY_LANGUAGE", "unknown")
    strategy = os.environ.get("RELEASE_STRATEGY", "stable")
    auto_prerelease = (
        os.environ.get("AUTO_PRERELEASE", "false").lower() == "true"
    )
    auto_draft = os.environ.get("AUTO_DRAFT", "false").lower() == "true"

    # Find the previous STABLE release tag for changelog diffing.
    #
    # Priority:
    # 1. PREVIOUS_VERSION env var (explicit override for parallel
    #    release lines like 1.x / 2.x / 3.x)
    # 2. Auto-detect: list all stable semver tags, exclude RC/alpha/beta,
    #    sort by version, take the second entry (first is the tag we're
    #    creating right now).
    previous_override = os.environ.get("PREVIOUS_VERSION", "").strip()
    if previous_override:
        last_tag = previous_override
    else:
        tag_list = _run_git(
            [
                "tag",
                "-l",
                "v*.*.*",
                "--sort=-v:refname",
            ]
        )
        stable_tags = [
            t
            for t in tag_list.stdout.strip().splitlines()
            if t.strip()
            and "-rc" not in t
            and "-alpha" not in t
            and "-beta" not in t
        ]
        # The first entry is the tag we just created (or the latest stable);
        # the second is the "previous release" we want the diff from.
        if len(stable_tags) >= 2:
            last_tag = stable_tags[1]
        elif len(stable_tags) == 1:
            last_tag = stable_tags[0]
        else:
            last_tag = ""

    if last_tag:
        log_args = [f"{last_tag}..HEAD"]
        header = f"### 📋 Commits since {last_tag}:\n"
    else:
        log_args = []
        header = "### 📋 Initial Release Commits:\n"

    commits = _run_git(
        ["log"] + log_args + ["--pretty=%s (%h)"]
    ).stdout.splitlines()
    commits = [entry for entry in commits if entry.strip()]

    lines = ["## 🚀 What's Changed", "", header]
    if commits:
        lines.extend(_cap_commit_lines(commits, CHANGELOG_COMMITS_BUDGET))
    else:
        lines.append("- No commits available")

    lines.extend(
        [
            "",
            "### 🎯 Release Information",
            f"- **Branch:** {branch}",
            f"- **Release Type:** {strategy}",
            f"- **Primary Language:** {primary_language}",
        ]
    )

    if auto_prerelease:
        lines.append(
            "\n⚠️ **This is a pre-release version** - use for testing purposes."
        )
    if auto_draft:
        lines.append(
            "\n📝 **This is a draft release** - review before making public."
        )

    changelog = "\n".join(lines) + "\n"
    # Hand the notes to later steps as a FILE, never as a step output that
    # gets expanded into an action input, env var or argv. A long release
    # (hundreds of commits) produced ~125 KB of notes, and Linux caps any
    # single env/argv string at 128 KiB (MAX_ARG_STRLEN), so the release
    # action died with "Argument list too long" after the release existed,
    # skipping changelog collection and draft cleanup.
    out_dir = Path(os.environ.get("RUNNER_TEMP") or ".") / "release-notes"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "changelog.md"
    out_file.write_text(changelog, encoding="utf-8")
    write_output("changelog_file", str(out_file))
    # Kept for an older reusable-release.yml paired with this script (the
    # scripts are checked out at the caller's ghcommon-ref, separately from
    # the workflow). Without it that workflow publishes an empty body.
    append_to_file("GITHUB_OUTPUT", "changelog_content<<EOF\n")
    append_to_file("GITHUB_OUTPUT", changelog)
    append_to_file("GITHUB_OUTPUT", "EOF\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Release workflow helper commands."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands = {
        "detect-languages": detect_languages,
        "release-strategy": release_strategy,
        "generate-version": generate_version,
        "generate-changelog": generate_changelog,
    }

    for command, handler in commands.items():
        subparsers.add_parser(command).set_defaults(handler=handler)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)
    handler(args)


if __name__ == "__main__":
    main()
