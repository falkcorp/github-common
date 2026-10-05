#!/usr/bin/env python3
# file: .github/scripts/parse_config_json.py
# version: 1.0.1
# guid: 2a1b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d
# last-edited: 2026-10-05

import json
import os
import sys


def main():
    """Parse CONFIG_JSON from the environment and emit its fields."""
    config_json = os.environ.get("CONFIG_JSON", "{}")
    try:
        config = json.loads(config_json)
    except Exception as e:
        print(f"::error::Failed to parse CONFIG_JSON: {e}")
        sys.exit(1)

    # Output the entire config as a JSON string for use in the workflow
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"config={json.dumps(config)}\n")

    print(f"Parsed config_json with {len(config)} keys")


if __name__ == "__main__":
    main()
