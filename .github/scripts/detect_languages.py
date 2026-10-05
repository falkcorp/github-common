#!/usr/bin/env python3
# file: .github/scripts/detect_languages.py
# version: 1.2.1
# guid: 4f6c9d88-2d4b-4a1e-9c61-3e0b2b9a7f11
# last-edited: 2026-10-05
"""Detect project languages and emit key=value lines for GitHub Actions outputs.

Enhanced to respect `.github/workflow-config.yaml` for language versions,
platforms, operating systems, and feature flags. Falls back to sensible
defaults when the config file or specific keys are absent.

The output format remains backward compatible so existing workflow jobs
(`release-*.yml`) continue to function without modification.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

CONFIG_PATH = ".github/workflow-config.yaml"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    return value


def load_build_config() -> dict[str, Any]:
    """Very small, dependency-free YAML subset parser for the build section.

    We avoid PyYAML to keep the workflow zero-install. Only the needed keys
    inside the top-level `build:` mapping are parsed. Commented lines or
    commented-out blocks are ignored.
    """
    if not os.path.exists(CONFIG_PATH):
        return {}

    build: dict[str, Any] = {}
    in_build = False
    current_list_key: str | None = None

    with open(CONFIG_PATH, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Detect leaving build section (new top-level key)
            if (
                in_build
                and not line.startswith(" ")
                and not stripped.startswith("build:")
            ):
                # Reached a new top-level key; stop parsing build
                break

            if stripped.startswith("build:"):
                in_build = True
                continue

            if not in_build:
                continue

            # Inside build section
            # List entry
            if current_list_key and stripped.startswith("- "):
                val = _strip_quotes(stripped[2:].strip())
                if val:
                    build.setdefault(current_list_key, []).append(val)
                continue

            # New key (possibly list or scalar)
            key_match = re.match(r"([A-Za-z0-9_]+):\s*(.*)$", stripped)
            if not key_match:
                continue
            key, remainder = key_match.groups()

            if remainder == "":  # list start or empty value
                current_list_key = (
                    key if key.endswith("s") else None
                )  # heuristic
                if current_list_key:
                    build.setdefault(current_list_key, [])
                continue

            # Scalar value
            current_list_key = None
            value_clean = _strip_quotes(remainder)
            if value_clean.lower() in {"true", "false"}:
                build[key] = value_clean.lower() == "true"
            else:
                build[key] = value_clean

    return build


build_cfg = load_build_config()
config_loaded = os.path.exists(CONFIG_PATH)


def exists_any(*paths: str) -> bool:
    """Return True if any of the given paths exists."""
    return any(os.path.exists(p) for p in paths)


has_go = exists_any("go.mod", "main.go")
has_python = (
    exists_any("pyproject.toml", "requirements.txt", "setup.py")
    or any(f.startswith("test_") for f in os.listdir("tests"))
    if os.path.isdir("tests")
    else False
)
has_frontend = exists_any("package.json", "yarn.lock", "pnpm-lock.yaml")
has_docker = exists_any(
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml"
)
has_rust = exists_any("Cargo.toml")
protobuf_needed = (
    (build_cfg.get("enable_protobuf") is True)
    or exists_any("buf.gen.yaml", "buf.yaml")
    or os.path.isdir("proto")
)

if has_rust:
    primary = "rust"
elif has_go:
    primary = "go"
elif has_python:
    primary = "python"
elif has_frontend:
    primary = "frontend"
else:
    primary = "unknown"


def build_matrix(
    versions: list[str], os_list: list[str], version_key: str
) -> dict[str, Any]:
    """Build a versions x OS include-matrix; the first entry is primary."""
    include: list[dict[str, Any]] = []
    if not versions or not os_list:
        return {"include": include}
    primary_set = False
    for v in versions:
        for os_name in os_list:
            entry = {"os": os_name, version_key: v, "primary": False}
            if not primary_set:
                entry["primary"] = True
                primary_set = True
            include.append(entry)
    return {"include": include}


go_versions = build_cfg.get("go_versions") or ["1.24"]
python_versions = build_cfg.get("python_versions") or ["3.13"]
raw_node_versions = build_cfg.get("node_versions")
if config_loaded:
    if raw_node_versions is None:
        has_frontend = False
        node_versions: list[str] = []
    else:
        node_versions = raw_node_versions or []
        if not node_versions:
            has_frontend = False
else:
    node_versions = ["20"] if has_frontend else []
operating_systems = build_cfg.get("operating_systems") or ["ubuntu-latest"]
platforms = build_cfg.get("platforms") or ["linux/amd64", "linux/arm64"]

go_matrix = (
    build_matrix(go_versions, operating_systems, "go-version")
    if has_go
    else {"include": []}
)
python_matrix = (
    build_matrix(python_versions, operating_systems, "python-version")
    if has_python
    else {"include": []}
)
frontend_matrix = (
    build_matrix(node_versions, operating_systems, "node-version")
    if has_frontend
    else {"include": []}
)

docker_matrix = (
    {
        "include": [
            {"platform": p, "os": operating_systems[0], "primary": i == 0}
            for i, p in enumerate(platforms)
        ]
    }
    if has_docker
    else {"include": []}
)


def emit(key: str, value: object) -> None:
    """Print a key=value line for GITHUB_OUTPUT."""
    print(f"{key}={value}")


emit("has-go", str(has_go).lower())
emit("has-python", str(has_python).lower())
emit("has-frontend", str(has_frontend).lower())
emit("has-docker", str(has_docker).lower())
emit("has-rust", str(has_rust).lower())
emit("protobuf-needed", str(protobuf_needed).lower())
emit("primary-language", primary)
emit("project-type", primary)
emit("go-matrix", json.dumps(go_matrix))
emit("python-matrix", json.dumps(python_matrix))
emit("frontend-matrix", json.dumps(frontend_matrix))
emit("docker-matrix", json.dumps(docker_matrix))
