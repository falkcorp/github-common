# file: tests/workflow_scripts/test_release_workflow.py
# version: 1.1.0
# guid: 543b49c0-5c64-4cea-a025-76de25f6b324
# last-edited: 2026-10-16

import argparse
import json
from pathlib import Path

import pytest
import release_workflow
import workflow_common


@pytest.fixture(autouse=True)
def reset_release_config_cache():
    workflow_common.reset_repository_config()
    yield
    workflow_common.reset_repository_config()


def _parse_outputs(path: Path) -> dict[str, str]:
    data = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data


def test_detect_languages_auto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example.com/test\n")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "Dockerfile").write_text("FROM busybox\n")
    (tmp_path / "proto").mkdir()
    (tmp_path / "proto" / "test.proto").write_text('syntax = "proto3";\n')

    output_file = tmp_path / "outputs.txt"
    config = {
        "languages": {
            "versions": {
                "go": ["1.20", "1.21"],
                "python": ["3.10", "3.11"],
                "rust": ["stable"],
                "node": ["18"],
            }
        },
        "build": {
            "platforms": {"os": ["ubuntu-latest"]},
            "docker": {"platforms": ["linux/amd64"]},
        },
    }
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    release_workflow.detect_languages(argparse.Namespace())

    outputs = _parse_outputs(output_file)
    assert outputs["has-go"] == "true"
    assert outputs["has-python"] == "true"
    assert outputs["has-docker"] == "true"
    assert outputs["protobuf-needed"] == "true"
    assert json.loads(outputs["go-matrix"])["go-version"] == ["1.20", "1.21"]
    assert json.loads(outputs["docker-matrix"])["platform"] == ["linux/amd64"]


def test_release_strategy_branch_defaults(monkeypatch, tmp_path):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("BRANCH_NAME", "develop")
    monkeypatch.setenv("INPUT_PRERELEASE", "false")
    monkeypatch.setenv("INPUT_DRAFT", "false")

    release_workflow.release_strategy(argparse.Namespace())
    outputs = _parse_outputs(output_file)
    assert outputs["strategy"] == "prerelease"
    assert outputs["auto-prerelease"] == "true"
    assert outputs["auto-draft"] == "false"


def test_generate_version_from_tag(monkeypatch, tmp_path):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("RELEASE_TYPE", "auto")
    monkeypatch.setenv("BRANCH_NAME", "main")
    monkeypatch.setenv("AUTO_PRERELEASE", "false")
    monkeypatch.setenv("AUTO_DRAFT", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")

    monkeypatch.setattr(release_workflow, "_latest_tag_from_api", lambda: "")
    monkeypatch.setattr(
        release_workflow, "_latest_tag_from_git", lambda: "v1.2.3"
    )

    def fake_run(args, check=False):
        cmd = tuple(args)
        if cmd[:2] == ("tag", "-l", "v1.2.4"):
            return subprocess.CompletedProcess(args, 0, "", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    import subprocess

    monkeypatch.setattr(release_workflow, "_run_git", fake_run)

    release_workflow.generate_version(argparse.Namespace())
    outputs = _parse_outputs(output_file)
    assert outputs["tag"] == "v1.2.4"


def test_generate_changelog(monkeypatch, tmp_path):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path / "runner-temp"))
    monkeypatch.setenv("BRANCH_NAME", "main")
    monkeypatch.setenv("PRIMARY_LANGUAGE", "go")
    monkeypatch.setenv("RELEASE_STRATEGY", "stable")
    monkeypatch.setenv("AUTO_PRERELEASE", "false")
    monkeypatch.setenv("AUTO_DRAFT", "true")

    import subprocess

    def fake_run(args, check=False):
        cmd = tuple(args)
        if cmd[:2] == ("describe", "--tags"):
            return subprocess.CompletedProcess(args, 0, "v1.0.0\n", "")
        if cmd[0] == "log":
            return subprocess.CompletedProcess(
                args,
                0,
                "feat: add feature (abc123)\nfix: bug fix (def456)\n",
                "",
            )
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(release_workflow, "_run_git", fake_run)

    release_workflow.generate_changelog(argparse.Namespace())
    outputs = _parse_outputs(output_file)
    # Workflows read the notes from the file; the inline copy stays only for
    # an older reusable-release.yml paired with this script.
    content = Path(outputs["changelog_file"]).read_text(encoding="utf-8")
    assert content in output_file.read_text(encoding="utf-8")
    assert "feat: add feature" in content
    assert "Release Type" in content


def test_cap_commit_lines_keeps_everything_under_budget():
    commits = ["feat: a (1)", "fix: b (2)"]
    assert release_workflow._cap_commit_lines(commits, 1000) == [
        "- feat: a (1)",
        "- fix: b (2)",
    ]


def test_cap_commit_lines_drops_oldest_and_says_how_many():
    commits = [f"fix: change number {i} ({i:07x})" for i in range(5000)]
    lines = release_workflow._cap_commit_lines(
        commits, release_workflow.CHANGELOG_COMMITS_BUDGET
    )
    body = "\n".join(lines)
    assert len(body) <= release_workflow.CHANGELOG_COMMITS_BUDGET
    # Newest first: the first commit survives, the oldest does not.
    assert lines[0] == f"- {commits[0]}"
    assert f"- {commits[-1]}" not in lines
    kept = len(lines) - 1
    assert lines[-1].startswith(f"- … and {5000 - kept} older commit(s)")


def test_generate_changelog_long_history_fits_github_body_limit(
    monkeypatch, tmp_path
):
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path / "runner-temp"))
    monkeypatch.setenv("PREVIOUS_VERSION", "v0.1.0")

    import subprocess

    # Multibyte subjects: a ~125 KB body like this is what overflowed the
    # 128 KiB env/argv string limit when passed as an action input.
    log = "".join(
        f"fix(ü): ✓ subject number {i} ({i:09x})\n" for i in range(6000)
    )

    def fake_run(args, check=False):
        if args[0] == "log":
            return subprocess.CompletedProcess(args, 0, log, "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(release_workflow, "_run_git", fake_run)

    release_workflow.generate_changelog(argparse.Namespace())
    content = Path(_parse_outputs(output_file)["changelog_file"]).read_text(
        encoding="utf-8"
    )
    # GitHub's release body limit is 125,000 characters; leave room for the
    # header/footer the workflow adds around these notes.
    assert len(content) < 120_000
    assert "older commit(s) not listed" in content


def test_cap_commit_lines_exact_fit_is_not_cut():
    commits = ["abc", "de"]
    # "- abc\n- de" is exactly 10 characters.
    assert release_workflow._cap_commit_lines(commits, 10) == ["- abc", "- de"]


def test_cap_commit_lines_oversized_newest_is_not_called_older():
    lines = release_workflow._cap_commit_lines(["x" * 500, "y"], 200)
    assert lines == [release_workflow._omitted_line(2, newest=True)]
    assert "older" not in lines[0]
