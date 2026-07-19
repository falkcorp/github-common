#!/usr/bin/env python3
# file: tests/workflow_scripts/test_generate_release_summary.py
# version: 1.0.0
# guid: 3b2c1d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e

"""Tests for the release summary generation script."""

from __future__ import annotations

from pathlib import Path

import generate_release_summary
import pytest


def test_generate_release_summary_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Script writes summary and success status."""
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    monkeypatch.setenv("SUMMARY_PRIMARY_LANGUAGE", "go")
    monkeypatch.setenv("SUMMARY_BUILD_TARGET", "all")
    monkeypatch.setenv("SUMMARY_RELEASE_TAG", "v1.2.3")
    monkeypatch.setenv("SUMMARY_RELEASE_STRATEGY", "stable")
    monkeypatch.setenv("SUMMARY_BRANCH", "main")
    monkeypatch.setenv("SUMMARY_GO_RESULT", "success")
    monkeypatch.setenv("SUMMARY_PYTHON_RESULT", "skipped")
    monkeypatch.setenv("SUMMARY_RUST_RESULT", "success")
    monkeypatch.setenv("SUMMARY_FRONTEND_RESULT", "skipped")
    monkeypatch.setenv("SUMMARY_DOCKER_RESULT", "success")
    monkeypatch.setenv("SUMMARY_RELEASE_RESULT", "success")
    monkeypatch.setenv("SUMMARY_PUBLISH_RESULT", "success")
    monkeypatch.setenv("SUMMARY_RELEASE_CREATED", "true")
    monkeypatch.setenv("SUMMARY_AUTO_PRERELEASE", "false")
    monkeypatch.setenv("SUMMARY_AUTO_DRAFT", "false")

    generate_release_summary.main()

    content = summary.read_text(encoding="utf-8")
    assert "Release created: v1.2.3" in content
    assert "| Go | success |" in content
    assert "✅ **All components completed successfully**" in content


def test_generate_release_summary_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Script records a component failure in the summary without exiting."""
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    monkeypatch.setenv("SUMMARY_PRIMARY_LANGUAGE", "go")
    monkeypatch.setenv("SUMMARY_BUILD_TARGET", "all")
    monkeypatch.setenv("SUMMARY_RELEASE_TAG", "v1.2.3")
    monkeypatch.setenv("SUMMARY_RELEASE_STRATEGY", "stable")
    monkeypatch.setenv("SUMMARY_BRANCH", "main")
    monkeypatch.setenv("SUMMARY_GO_RESULT", "failure")
    monkeypatch.setenv("SUMMARY_PYTHON_RESULT", "skipped")
    monkeypatch.setenv("SUMMARY_RUST_RESULT", "success")
    monkeypatch.setenv("SUMMARY_FRONTEND_RESULT", "skipped")
    monkeypatch.setenv("SUMMARY_DOCKER_RESULT", "success")
    monkeypatch.setenv("SUMMARY_RELEASE_RESULT", "success")
    monkeypatch.setenv("SUMMARY_PUBLISH_RESULT", "skipped")
    monkeypatch.setenv("SUMMARY_RELEASE_CREATED", "false")
    monkeypatch.setenv("SUMMARY_AUTO_PRERELEASE", "false")
    monkeypatch.setenv("SUMMARY_AUTO_DRAFT", "false")

    # Deliberately does NOT exit non-zero: the script records the failure in the
    # step summary and lets the CI summary job decide the overall run status.
    # See the comment in generate_release_summary.main().
    generate_release_summary.main()

    content = summary.read_text(encoding="utf-8")
    assert "❌ **Some components failed**" in content
