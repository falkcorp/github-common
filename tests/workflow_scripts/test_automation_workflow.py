#!/usr/bin/env python3
# file: tests/workflow_scripts/test_automation_workflow.py
# version: 1.2.0
# guid: d9f5c8b3-2c4d-4e5f-9a7b-3c2d1f0e1a2b

"""Tests for automation_workflow helper module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

import automation_workflow
import jwt
import pytest

TEST_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAvcRdut4cOeDlhJ+km5vyDbD0+v4pW7vKSTphf8mvkjm4q5F4
b+POtcObMXbQSggl2YXM59GElBVJODE6NswZJ7MgqgiPdrEBmM/rC+2vzh2P3Suw
fT+qo9ezYYdpkOV/Nrd80Dn3gohOIM2gy8bn/pY61Dhl1jp+nPai6+Oq/04csk3f
ERZECw97BeEzLi0Ckh7hyJUO1GEPH9RKcO+ykALX8aPWQ03LyHoQqXAWmJ/JYDFt
iygKjkq8N6OEYbyLJqQCM+TRn3a99QMyNlH4ZDukGWTs58b7ZLU9tyFk/YvjFipm
WoQO2D6OkAReJesNTyWbRPNps5KlPEZcFbTrAwIDAQABAoIBAQCPcBstAXAya4Tx
Hz5sBI8MvEIgafbXCPYZLdC+p7NXAtxMitOPN5FqoKTw2Y8NNmVtqw4794mP6RsE
J2mKO/GTqXk6LOhL3fWIDTjsNkgZswyoL7rioToZSBSl1pX72Qy0TjNArWAhwWfU
sbkl7n4zWFi1Sr/nEyXa/S4ewWLiQFpwlC1Ss7UV+byx0Vgl0OlSlbXDjmFelVOf
+tUC1FTE68Kod5kVgx8SK6c5LmoQ+YU0gGZkie+qIK1d8/Gsd1UpYN/aFCpeP/Ba
4FnvqTGykcTKui+58FTL2LLmOb60G+A8cZoOK0g+ZG6LI6PrTOIkhf2jfHolkQ4t
Q7/Ndk9hAoGBAOHkFuOXpm8e61ezeSOs8gWOK4610FgNKKD2n3+N3ybyE3XQO/53
SjM2BRCYirglgbSHjZA62VjHPloN4JyJ84FBOrcUZXeOyVl3Ljoxm5KxoTa4nypp
B5yxXFSSPTntj9OwDSWtoD/oDIkRdYiJ+HxPlojtkjInX9//4FfQZ20xAoGBANcP
pZ8Vhsx8JkYlLAvkQv9vxGtUcNW9L5+LG942GZYGEIreFSouqtXHVgBd2OHTKgn2
b1AqFuQSHWdfzh8u75u4DtrUupav5ba/zRQXEr1jFUKXPeZRajHZDKZm0xliS5Ir
dxKRpfuxjWZY62VCpJIjZbJsaY38JgR70EnAXT5zAoGAekxdQBdo2pyo2jCnE3Od
DPjuCDPTeviU2KDttcd/27wQYSa+dITtPVCv6U5NPGnCEZWaRU43QmONFICS7O2b
Uo2YVmrKjLJXvQJTmtok2oUlPVUzh2iZ4HH+BSOv1l8SEZAtbgrUygS+VK+JLMVW
LSeB3tyQ3GqI8+O6+JAyjuECgYAu8FtVvX0OZIp2BOb4MXnuBpb4VhXKkOA0Ekii
12v+MpSpuo8kBcuDnV5H9jPAFja2tfLVrFoSrWF9jouOgtAJTMLxQDz5ZqrcmEBK
gj6010tsnVYFTv++oYEBULACelHENXhntSJlLPuPuxiloUYKH2+y4baoJsCleeCc
OEAhwQKBgCrwR7X9TbJwI9TyJMsBC9wyFDR8A/tsPOe2C1kn3J30Ax/79STX26Ls
ACTnQCtPUYOs2oQ+cxX+Cq7qNt2pyZLVjPY7Xe7OlSC6IogG2uUBOHdpJ9+/gPDz
i+xR6BLV92iFw+ejYxVNhDFEb7QX2f57dFHfp/+W2rPexCU4hWNx
-----END RSA PRIVATE KEY-----
"""

TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvcRdut4cOeDlhJ+km5vy
DbD0+v4pW7vKSTphf8mvkjm4q5F4b+POtcObMXbQSggl2YXM59GElBVJODE6NswZ
J7MgqgiPdrEBmM/rC+2vzh2P3SuwfT+qo9ezYYdpkOV/Nrd80Dn3gohOIM2gy8bn
/pY61Dhl1jp+nPai6+Oq/04csk3fERZECw97BeEzLi0Ckh7hyJUO1GEPH9RKcO+y
kALX8aPWQ03LyHoQqXAWmJ/JYDFtiygKjkq8N6OEYbyLJqQCM+TRn3a99QMyNlH4
ZDukGWTs58b7ZLU9tyFk/YvjFipmWoQO2D6OkAReJesNTyWbRPNps5KlPEZcFbTr
AwIDAQAB
-----END PUBLIC KEY-----
"""


def test_build_app_jwt_encodes_expected_payload() -> None:
    """build_app_jwt produces RS256 token with correct claims."""
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    token = automation_workflow.build_app_jwt(
        app_id=12345,
        private_key=TEST_PRIVATE_KEY,
        expires_in=300,
        now=now,
    )
    decoded = jwt.decode(
        token,
        TEST_PUBLIC_KEY,
        algorithms=["RS256"],
        options={
            "verify_aud": False,
            "verify_exp": False,
        },
    )
    assert decoded["iss"] == "12345"
    assert decoded["iat"] == int(now.timestamp())
    assert decoded["exp"] == int((now + timedelta(seconds=300)).timestamp())


def test_generate_cache_strategy_includes_fingerprints(tmp_path: Path) -> None:
    """generate_cache_strategy hashes files and directories."""
    file_a = tmp_path / "a.txt"
    file_a.write_text("alpha\n", encoding="utf-8")
    dir_b = tmp_path / "nested"
    dir_b.mkdir()
    (dir_b / "b.txt").write_text("bravo\n", encoding="utf-8")

    strategy = automation_workflow.generate_cache_strategy(
        "python",
        [file_a, dir_b],
        namespace="ci",
        extras={"python": "3.13"},
        cache_paths=[tmp_path / "cache"],
    )

    assert strategy.key.startswith("python-")
    assert "python" in strategy.metadata["extras"]
    fingerprints = strategy.metadata["fingerprints"]
    assert str(file_a) in fingerprints
    assert str(dir_b) in fingerprints
    # ensure restore keys trimmed consistently
    assert all(strategy.key.startswith(key) for key in strategy.restore_keys)
    assert str(tmp_path / "cache") in strategy.paths


def test_build_cache_plan_returns_defaults() -> None:
    """build_cache_plan returns default files and paths for language."""
    plan = automation_workflow.build_cache_plan("go")
    assert plan.language == "go"
    assert plan.files == ("go.mod", "go.sum")
    assert "~/.cache/go-build" in plan.paths
    assert "~/go/pkg/mod" in plan.paths


def test_collect_workflow_metrics_groups_runs() -> None:
    """collect_workflow_metrics aggregates run data."""
    runs: list[dict[str, Any]] = [
        {
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "duration_seconds": 30,
            "run_started_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:30Z",
            "cache": {"hit": True},
        },
        {
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "duration_seconds": 60,
            "run_started_at": "2024-01-02T00:00:00Z",
            "updated_at": "2024-01-02T00:01:00Z",
            "cache": {"hit": False},
        },
        {
            "name": "Docs",
            "status": "completed",
            "conclusion": "success",
            "duration_seconds": 45,
            "run_started_at": "2024-01-02T02:00:00Z",
            "updated_at": "2024-01-02T02:00:45Z",
        },
    ]

    metrics = automation_workflow.collect_workflow_metrics(runs)

    assert metrics.total_runs == 3
    assert pytest.approx(metrics.success_rate, rel=1e-6) == 2 / 3
    assert (
        pytest.approx(metrics.average_duration, rel=1e-6) == (30 + 60 + 45) / 3
    )
    ci_summary = metrics.workflows["CI"]
    assert ci_summary.runs == 2
    assert ci_summary.failures == 1
    assert ci_summary.cache_hit_rate == 0.5


def test_detect_self_healing_actions_flags_failures() -> None:
    """detect_self_healing_actions highlights low success and cache rates."""
    failure_runs = [
        {
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "duration_seconds": 25,
            "run_started_at": "2024-02-01T00:00:00Z",
            "updated_at": "2024-02-01T00:00:25Z",
            "cache_hit": False,
        },
        {
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "duration_seconds": 30,
            "run_started_at": "2024-02-02T00:00:00Z",
            "updated_at": "2024-02-02T00:00:30Z",
            "cache_hit": False,
        },
        {
            "name": "CI",
            "status": "completed",
            "conclusion": "failure",
            "duration_seconds": 40,
            "run_started_at": "2024-02-03T00:00:00Z",
            "updated_at": "2024-02-03T00:00:40Z",
            "cache_hit": False,
        },
    ]
    metrics = automation_workflow.collect_workflow_metrics(failure_runs)
    actions = automation_workflow.detect_self_healing_actions(metrics)

    slugs = {action.slug for action in actions}
    assert "CI-failure-streak" in slugs
    cache_action = next(
        action for action in actions if action.slug.startswith("CI-cache")
    )
    assert cache_action.severity == "medium"


def test_filter_runs_by_lookback_filters_old_entries() -> None:
    """filter_runs_by_lookback drops runs older than the cutoff."""
    now = datetime(2024, 2, 10, tzinfo=timezone.utc)
    runs = [
        {"name": "CI", "run_started_at": "2024-02-09T00:00:00Z"},
        {"name": "CI", "run_started_at": "2024-01-20T00:00:00Z"},
        {"name": "Docs", "run_started_at": "2024-02-08T12:00:00Z"},
    ]
    filtered = automation_workflow.filter_runs_by_lookback(runs, 10, now=now)
    assert len(filtered) == 2
    assert all(
        item["name"] != "CI" or item["run_started_at"].startswith("2024-02")
        for item in filtered
    )


def test_main_cache_key_outputs_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """cache-key command prints JSON payload."""
    file_a = tmp_path / "example.txt"
    file_a.write_text("data\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "outputs.txt"))

    exit_code = automation_workflow.main(
        [
            "cache-key",
            "--prefix",
            "ci",
            "--files",
            str(file_a),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["key"].startswith("ci-")
    assert payload["metadata"]["fingerprints"][str(file_a)]


def test_cache_key_includes_branch_and_writes_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """cache-key command includes branch component and writes GitHub outputs."""
    file_a = tmp_path / "example.txt"
    file_a.write_text("data\n", encoding="utf-8")
    output_file = tmp_path / "outputs.txt"
    monkeypatch.setenv("GITHUB_REF_NAME", "Feature/New-Thing")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    exit_code = automation_workflow.main(
        [
            "cache-key",
            "--prefix",
            "ci",
            "--files",
            str(file_a),
            "--paths",
            str(tmp_path / "cache"),
            "--include-branch",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["branch"] == "feature-new-thing"
    assert payload["key"].startswith("ci-feature-new-thing-")
    outputs = output_file.read_text(encoding="utf-8")
    assert "cache-key=ci-feature-new-thing-" in outputs
    # restore-keys is a newline-joined list, so write_output emits it in the
    # heredoc form GitHub Actions requires for multiline values
    # (name<<DELIM / value / DELIM) rather than as name=value.
    assert "restore-keys<<" in outputs
    for restore_key in payload["restore_keys"]:
        assert restore_key in outputs
    assert "cache-paths=" in outputs
    assert "cache-branch=feature-new-thing" in outputs


def test_cache_plan_writes_github_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """cache-plan writes files/paths to GitHub outputs."""
    output_file = tmp_path / "metadata.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    exit_code = automation_workflow.main(
        [
            "cache-plan",
            "--language",
            "python",
            "--github-output",
            "--extra-file",
            "poetry.lock",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["language"] == "python"
    assert "poetry.lock" in payload["files"]
    outputs = output_file.read_text(encoding="utf-8")
    assert "files=requirements.txt,pyproject.toml,poetry.lock" in outputs
    assert "./.venv" in outputs


def test_fetch_recent_workflow_runs_uses_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """fetch_recent_workflow_runs calls the provided session."""

    class StubResponse:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload
            self.status_code = 200

        def json(self) -> dict[str, Any]:
            return self._payload

    class StubSession:
        def __init__(self) -> None:
            self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

        def get(self, *args: Any, **kwargs: Any) -> StubResponse:
            self.calls.append((args, kwargs))
            return StubResponse({"workflow_runs": [{"name": "CI"}]})

    session = StubSession()
    runs = automation_workflow.fetch_recent_workflow_runs(
        "owner/repo",
        token="token",
        session=session,
        pages=1,
    )

    assert runs == [{"name": "CI"}]
    assert session.calls  # ensures request executed
