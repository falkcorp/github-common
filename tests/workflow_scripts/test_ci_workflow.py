# file: tests/workflow_scripts/test_ci_workflow.py
# version: 1.0.0
# guid: be8f15eb-d640-417d-8c19-bb923f338f54
# last-edited: 2026-10-20

import argparse
import json
import subprocess
from typing import Any

import ci_workflow
import pytest


@pytest.fixture(autouse=True)
def reset_config_cache():
    ci_workflow.get_repository_config.cache_clear()


def test_debug_filter_outputs(monkeypatch, capsys):
    env_values = {
        "CI_GO_FILES": "true",
        "CI_FRONTEND_FILES": "false",
        "CI_PYTHON_FILES": "true",
        "CI_RUST_FILES": "false",
        "CI_DOCKER_FILES": "false",
        "CI_DOCS_FILES": "true",
        "CI_WORKFLOW_FILES": "true",
        "CI_LINT_FILES": "false",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, value)

    ci_workflow.debug_filter(argparse.Namespace())
    output = capsys.readouterr().out
    assert "Go files changed: true" in output
    assert "Docs files changed: true" in output


def test_determine_execution_sets_outputs(tmp_path, monkeypatch):
    output_file = tmp_path / "output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("GITHUB_HEAD_COMMIT_MESSAGE", "fix bug [skip ci]")
    monkeypatch.setenv("CI_GO_FILES", "true")
    monkeypatch.setenv("CI_FRONTEND_FILES", "false")
    monkeypatch.setenv("CI_PYTHON_FILES", "true")
    monkeypatch.setenv("CI_RUST_FILES", "false")
    monkeypatch.setenv("CI_DOCKER_FILES", "true")

    ci_workflow.determine_execution(argparse.Namespace())
    lines = output_file.read_text().splitlines()
    assert "skip_ci=true" in lines
    assert "should_test_go=true" in lines
    assert "should_test_frontend=false" in lines


class DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


def test_wait_for_pr_automation_completed(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("TARGET_SHA", "abc123")
    monkeypatch.setenv("WORKFLOW_NAME", "PR Automation")
    monkeypatch.setenv("MAX_ATTEMPTS", "1")

    def fake_get(url: str, **kwargs):
        assert "owner/repo" in url
        return DummyResponse(
            200,
            {
                "workflow_runs": [
                    {
                        "head_sha": "abc123",
                        "name": "PR Automation",
                        "status": "completed",
                    }
                ]
            },
        )

    monkeypatch.setattr(ci_workflow, "_http_get", fake_get)
    ci_workflow.wait_for_pr_automation(argparse.Namespace())
    captured = capsys.readouterr().out
    assert "✅ PR automation has completed" in captured


def test_load_super_linter_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "super-linter-ci.env").write_text("FOO=bar\n", encoding="utf-8")
    env_file = tmp_path / "env.txt"
    output_file = tmp_path / "output.txt"

    monkeypatch.setenv("EVENT_NAME", "push")
    monkeypatch.setenv("CI_ENV_FILE", "super-linter-ci.env")
    monkeypatch.setenv("PR_ENV_FILE", "super-linter-pr.env")
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    ci_workflow.load_super_linter_config(argparse.Namespace())
    assert env_file.read_text() == "FOO=bar\n"
    assert "config-file=super-linter-ci.env" in output_file.read_text()


def test_go_setup_skips_without_go_mod(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    def fake_run(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("go commands should not run")

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.go_setup(argparse.Namespace())
    assert "skipping Go step" in capsys.readouterr().out


def test_go_test_runs_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text(
        "module example.com/test\n", encoding="utf-8"
    )
    commands = []

    def fake_run(cmd, check=False, capture_output=False, text=False, **kwargs):
        commands.append((tuple(cmd), check, capture_output))
        if "-func" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="total: (statements) 75.0%\n"
            )
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setenv("COVERAGE_THRESHOLD", "70")
    monkeypatch.delenv("REPOSITORY_CONFIG", raising=False)
    ci_workflow.get_repository_config.cache_clear()
    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    monkeypatch.setattr(ci_workflow.shutil, "which", lambda name: "go")

    ci_workflow.go_test(argparse.Namespace())
    go_commands = [cmd for cmd, *_ in commands if cmd and cmd[0] == "go"]
    assert any("test" in cmd for cmd in go_commands)
    assert any("tool" in cmd for cmd in go_commands)


def test_python_run_tests_skips_when_no_tests(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    commands = []

    def fake_run(cmd, check=False, **kwargs):
        commands.append(tuple(cmd))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.python_install(argparse.Namespace())
    ci_workflow.python_run_tests(argparse.Namespace())
    assert any("pip" in part for cmd in commands for part in cmd)
    assert "ℹ️ No Python tests found" in capsys.readouterr().out


def test_python_lint_skips_without_changed_files(tmp_path, monkeypatch, capsys):
    """An empty tree has no changed Python files, so linting is skipped.

    python_lint only lints files the commit touched. With nothing changed it
    returns before the "no Python sources at all" check, so that is the message
    asserted here.
    """
    monkeypatch.chdir(tmp_path)
    ci_workflow.python_lint(argparse.Namespace())
    assert "No Python changes detected for linting" in capsys.readouterr().out


def test_rust_format_skips_without_cargo(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    ci_workflow.rust_format(argparse.Namespace())
    assert "No Cargo.toml" in capsys.readouterr().out


def test_rust_clippy_runs_with_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "example"\nversion = "0.1.0"\n', encoding="utf-8"
    )

    commands = []

    def fake_run(cmd, check=True, **kwargs):
        commands.append((tuple(cmd), check))
        return subprocess.CompletedProcess(cmd, 0)

    for env_var in (
        "CLIPPY_ALL_FEATURES",
        "CLIPPY_FEATURES",
        "CLIPPY_NO_DEFAULT_FEATURES",
        "CLIPPY_EXTRA_ARGS",
    ):
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.rust_clippy(argparse.Namespace())

    assert commands, "expected cargo clippy to run"
    cmd, check = commands[0]
    assert check is True
    assert cmd[:3] == ("cargo", "clippy", "--all-targets")
    assert "--" in cmd
    dash_index = cmd.index("--")
    assert cmd[dash_index + 1 : dash_index + 3] == ("-D", "warnings")


def test_rust_clippy_uses_environment_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname="test"\n', encoding="utf-8"
    )

    commands = []

    def fake_run(cmd, check=True, **kwargs):
        commands.append(tuple(cmd))
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setenv("CLIPPY_ALL_FEATURES", "true")
    monkeypatch.setenv("CLIPPY_FEATURES", "extra")
    monkeypatch.setenv("CLIPPY_NO_DEFAULT_FEATURES", "true")
    monkeypatch.setenv("CLIPPY_EXTRA_ARGS", "--workspace -- -Wclippy::all")

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.rust_clippy(argparse.Namespace())

    assert commands, "expected cargo clippy command to be executed"
    cmd = commands[0]
    assert "--all-features" in cmd
    assert "--features" in cmd
    features_index = cmd.index("--features")
    assert cmd[features_index + 1] == "extra"
    assert "--no-default-features" in cmd
    # Extra args should be appended exactly and should not include default warning flag.
    assert "-D" not in cmd
    assert "--workspace" in cmd


def test_go_test_uses_config_threshold(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text(
        "module example.com/test\n", encoding="utf-8"
    )

    config = {"testing": {"coverage": {"threshold": 90}}}
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    ci_workflow.get_repository_config.cache_clear()

    commands = []

    def fake_run(cmd, check=False, capture_output=False, text=False, **kwargs):
        commands.append((tuple(cmd), capture_output))
        if "-func" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="total: (statements) 95.0%\n"
            )
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    monkeypatch.setattr(ci_workflow.shutil, "which", lambda name: "go")

    ci_workflow.go_test(argparse.Namespace())
    assert commands, "expected go commands to execute"


def test_generate_matrices_uses_repository_config(tmp_path, monkeypatch):
    config = {
        "languages": {
            "versions": {
                "go": ["1.22", "1.23"],
                "python": ["3.11", "3.12"],
                "rust": ["stable"],
                "node": ["20"],
            }
        },
        "build": {"platforms": {"os": ["ubuntu-latest", "macos-latest"]}},
        "testing": {"coverage": {"threshold": 85}},
    }
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("REPOSITORY_CONFIG", json.dumps(config))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("FALLBACK_GO_VERSION", "1.24")
    monkeypatch.setenv("FALLBACK_PYTHON_VERSION", "3.13")
    monkeypatch.setenv("FALLBACK_RUST_VERSION", "stable")
    monkeypatch.setenv("FALLBACK_NODE_VERSION", "22")
    monkeypatch.setenv("FALLBACK_COVERAGE_THRESHOLD", "80")
    ci_workflow.get_repository_config.cache_clear()

    ci_workflow.generate_matrices(argparse.Namespace())

    outputs = dict(
        line.split("=", 1) for line in output_file.read_text().splitlines()
    )
    go_matrix = json.loads(outputs["go-matrix"])
    python_matrix = json.loads(outputs["python-matrix"])
    coverage_threshold = outputs["coverage-threshold"]

    assert go_matrix["include"][0]["go-version"] == "1.22"
    assert python_matrix["include"][0]["python-version"] == "3.11"
    assert python_matrix["include"][0]["os"] == "ubuntu-latest"
    assert any(
        entry["os"] == "macos-latest" for entry in python_matrix["include"]
    )
    assert coverage_threshold == "85"


def test_generate_ci_summary(tmp_path, monkeypatch):
    summary_path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_path))
    monkeypatch.setenv("JOB_DETECT_CHANGES", "success")
    monkeypatch.setenv("JOB_WORKFLOW_LINT", "success")
    monkeypatch.setenv("JOB_WORKFLOW_SCRIPTS", "skipped")
    monkeypatch.setenv("JOB_GO", "success")
    monkeypatch.setenv("JOB_PYTHON", "skipped")
    monkeypatch.setenv("JOB_RUST", "failure")
    monkeypatch.setenv("JOB_FRONTEND", "success")
    monkeypatch.setenv("JOB_DOCKER", "skipped")
    monkeypatch.setenv("JOB_DOCS", "skipped")
    monkeypatch.setenv("CI_GO_FILES", "true")
    monkeypatch.setenv("CI_PYTHON_FILES", "false")
    monkeypatch.setenv("CI_RUST_FILES", "true")
    monkeypatch.setenv("CI_FRONTEND_FILES", "false")
    monkeypatch.setenv("CI_DOCKER_FILES", "false")
    monkeypatch.setenv("CI_DOCS_FILES", "true")
    monkeypatch.setenv("CI_WORKFLOW_FILES", "false")
    monkeypatch.setenv("CI_WORKFLOW_YAML_FILES", "true")
    monkeypatch.setenv("CI_WORKFLOW_SCRIPT_FILES", "false")
    monkeypatch.setenv("CI_LINT_FILES", "true")

    ci_workflow.generate_ci_summary(argparse.Namespace())
    content = summary_path.read_text()
    assert "CI Pipeline Summary" in content
    assert "| Rust CI | failure |" in content
    assert "- Workflow YAML: true" in content
    assert "- Workflow Scripts: false" in content
    assert "- Lint Config: true" in content


def test_check_ci_status_failure(monkeypatch):
    monkeypatch.setenv("JOB_WORKFLOW_LINT", "success")
    monkeypatch.setenv("JOB_WORKFLOW_SCRIPTS", "skipped")
    monkeypatch.setenv("JOB_GO", "success")
    monkeypatch.setenv("JOB_PYTHON", "failure")
    monkeypatch.setenv("JOB_RUST", "success")
    monkeypatch.setenv("JOB_FRONTEND", "success")
    monkeypatch.setenv("JOB_DOCKER", "skipped")
    monkeypatch.setenv("JOB_DOCS", "skipped")
    with pytest.raises(SystemExit):
        ci_workflow.check_ci_status(argparse.Namespace())


def _lint_repo(tmp_path, monkeypatch):
    """A git repo whose last commit touched one Python file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ok.py").write_text('"""Doc."""\n', encoding="utf-8")
    for cmd in (
        ["git", "init", "-q"],
        ["git", "add", "ok.py"],
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-qm",
            "x",
        ],
    ):
        subprocess.run(cmd, check=True)  # noqa: S603


def test_python_lint_installs_pinned_ruff_and_runs_via_interpreter(
    tmp_path, monkeypatch
):
    """A mismatched ruff is replaced by ruff==RUFF_VERSION and run as python -m ruff."""
    _lint_repo(tmp_path, monkeypatch)
    monkeypatch.delenv("RUFF_VERSION", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    state = {"installed": "0.0.1"}
    commands: list[list[str]] = []
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == [ci_workflow.sys.executable, "-m", "ruff"]:
            commands.append(list(cmd))
            if cmd[3] == "--version":
                return subprocess.CompletedProcess(
                    cmd, 0, stdout=f"ruff {state['installed']}\n"
                )
            return subprocess.CompletedProcess(cmd, 0)
        if "pip" in cmd:
            commands.append(list(cmd))
            state["installed"] = cmd[-1].split("==")[1]
            return subprocess.CompletedProcess(cmd, 0)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.python_lint(argparse.Namespace())

    installs = [c for c in commands if "pip" in c]
    assert installs == [
        [
            ci_workflow.sys.executable,
            "-m",
            "pip",
            "install",
            f"ruff=={ci_workflow.RUFF_VERSION}",
        ]
    ]
    assert ci_workflow.RUFF_VERSION == "0.17.0"
    ran = [c[3] for c in commands if c[3] in ("format", "check")]
    assert ran == ["format", "check"]


def test_python_lint_honors_ruff_version_override(tmp_path, monkeypatch):
    _lint_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("RUFF_VERSION", "0.16.10")
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
    installs: list[str] = []
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if "pip" in cmd:
            installs.append(cmd[-1])
            return subprocess.CompletedProcess(cmd, 0)
        if cmd[:3] == [ci_workflow.sys.executable, "-m", "ruff"]:
            if cmd[3] == "--version":
                version = "0.16.10" if installs else "0.0.1"
                return subprocess.CompletedProcess(
                    cmd, 0, stdout=f"ruff {version}\n"
                )
            return subprocess.CompletedProcess(cmd, 0)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    ci_workflow.python_lint(argparse.Namespace())
    assert installs == ["ruff==0.16.10"]


def test_ensure_ruff_fails_loudly_on_version_mismatch(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="ruff 9.9.9\n")

    monkeypatch.setattr(ci_workflow.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match=r"expected ruff 0\.17\.0"):
        ci_workflow._ensure_ruff("0.17.0")
