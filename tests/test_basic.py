#!/usr/bin/env python3
"""Basic test suite for ghcommon repository.

This is a shared configuration repository that contains workflow
templates and scripts but doesn't have a main Python package to test.
This file ensures CI passes by providing minimal test coverage.
"""

import os
import sys
import unittest

# Add the parent directory to Python path for importing scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests."""

    def test_imports_work(self):
        """Test that we can import standard libraries."""
        import json
        import os

        # Test that json works
        test_data = {"test": "data"}
        json_str = json.dumps(test_data)
        self.assertIn("test", json_str)

        # Test that os works
        self.assertTrue(os.path.exists("."))
        self.assertTrue(True)

    def test_repository_structure(self):
        """Test that key repository files exist."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Check for key files
        expected_files = [
            ".github/workflows",
            "requirements.txt",
            "README.md",
            "LICENSE",
        ]

        for file_path in expected_files:
            full_path = os.path.join(repo_root, file_path)
            self.assertTrue(
                os.path.exists(full_path),
                f"Expected file/directory {file_path} not found",
            )

    def test_requirements_readable(self):
        """Test that requirements.txt is readable."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        requirements_path = os.path.join(repo_root, "requirements.txt")

        with open(requirements_path) as f:
            content = f.read()
            self.assertIn("requests", content)


class TestWorkflowIntegrity(unittest.TestCase):
    """Test workflow file integrity."""

    def test_workflow_files_exist(self):
        """Test that key workflow files exist."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workflows_dir = os.path.join(repo_root, ".github", "workflows")

        # matrix-build.yml was intentionally removed as deprecated in 4b41a69;
        # it is not a missing file, so it is not expected here.
        expected_workflows = ["ci.yml", "security.yml"]

        for workflow in expected_workflows:
            workflow_path = os.path.join(workflows_dir, workflow)
            self.assertTrue(
                os.path.exists(workflow_path),
                f"Expected workflow {workflow} not found",
            )


if __name__ == "__main__":
    unittest.main()
