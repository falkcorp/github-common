#!/usr/bin/env python3
# file: .github/scripts/run_buf_generate.py
# version: 1.0.1
# guid: 8c5b2d4e-3f7a-45d1-9e2f-1b6c7d8e9f01
# last-edited: 2026-10-05
"""Run buf generate with basic safety checks and clearer logging."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    """Run `buf generate` when buf.gen.yaml exists; return the exit code."""
    if not os.path.exists("buf.gen.yaml"):
        print("No buf.gen.yaml found, skipping generation")
        return 0
    print("Running buf generate...")
    proc = subprocess.run(["buf", "generate"], check=False, text=True)
    if proc.returncode != 0:
        print("buf generate failed", file=sys.stderr)
        return proc.returncode
    print("buf generate completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
