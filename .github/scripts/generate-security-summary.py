#!/usr/bin/env python3
# file: .github/scripts/generate-security-summary.py
# version: 1.0.1
# guid: sec-sum-gen-2025-12-07
# last-edited: 2026-10-05

"""Generate security scan summary for GitHub Actions.

This script reads environment variables for security scan results
and generates a formatted summary in GitHub Actions step summary format.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys


def main() -> int:
    """Generate security summary from environment variables."""
    results = {
        "CodeQL Analysis": os.environ.get("RESULT_CODEQL", "skipped"),
        "Dependency Review": os.environ.get("RESULT_DEP_REVIEW", "skipped"),
        "Security Audit": os.environ.get("RESULT_SECURITY_AUDIT", "skipped"),
    }

    summary_lines = [
        "## Security Scan Summary",
        "",
        "| Scan Type | Status |",
        "|-----------|--------|",
    ]

    for label, status in results.items():
        summary_lines.append(f"| {label} | {status} |")

    warning_required = any(status == "failure" for status in results.values())
    summary_lines.append("")
    if warning_required:
        summary_lines.append(
            "⚠️ **Security issues detected. Please review the scan results.**"
        )
    else:
        summary_lines.append("✅ **All security scans passed.**")

    summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return 1 if warning_required else 0


if __name__ == "__main__":
    sys.exit(main())
