### Fixed

- reusable-ci: gha-ci-workflow-helpers is pinned to v1.1.7-rc.8 (was a v1.1.4-labelled SHA). Under the old pin the `frontend-run` command exited 0 when the npm script failed, so a failing frontend unit or E2E run was reported as a pass; it now fails the step.
