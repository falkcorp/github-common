# Changelog

## [Unreleased]

### Fixed

#### `reusable-release.yml` — ghcommon workflow-scripts checkout pointed at the pre-migration `jdfalk/ghcommon` repo

All three "Checkout ghcommon workflow scripts" steps hardcoded
`repository: jdfalk/ghcommon`, which stopped existing once this repo moved to
`falkcorp/github-common` — every release/prerelease run's "Create GitHub
Release" job failed with
`unable to access 'https://github.com/jdfalk/ghcommon/': The requested URL returned error: 400`.
Updated all three to `repository: falkcorp/github-common`.

### Added

#### `reusable-release.yml` — `go-run-linters` input forwards to `gha-release-go`'s `run-linters`

Consumer repos whose Go code requires a `GOEXPERIMENT` value (e.g. `jsonv2`)
could set `go-experiment` but had no way to skip the release workflow's
redundant `go vet` pass — `gha-release-go`'s lint step doesn't currently set
`GOEXPERIMENT` from its `go-experiment` input, so any repo relying on that
experiment fails `go vet` on every release even though CI already vetted the
same commit correctly. Added `go-run-linters` (default `true`, preserves
existing behavior) so callers can pass `go-run-linters: false` until the root
cause is fixed upstream in `gha-release-go`.

### Fixed

#### `reusable-triage-poll.yml` — re-pinned to a valid image tag; auto-updater now covers it too

`reusable-triage-poll.yml` was pinned to
`ghcr.io/falkcorp/burndown-runner-image:d558a3367025991ebe86e43e46b4d9f73da39b88`,
a tag that no longer existed in the registry (`docker pull` →
`manifest unknown`) — every 30-min triage-poll cron run failed at the image-pull
step, silently starving the pipeline of triaged tasks for an unknown duration.
Root cause: `burndown-runner-image`'s release workflow auto-updates the image
pin in `reusable-burndown.yml` on every image release, but never touched
`reusable-triage-poll.yml`, so this file's pin was guaranteed to drift stale as
soon as any newer image shipped. Re-pinned to `ob-20cdfe3` (verified live) and
extended the auto-updater's `PINNED_FILES` list
(`falkcorp/burndown-runner-image@330037a`) so future releases keep both files in
sync.

## [v1.11.2] — 2026-06-10

### Fixed

#### `reusable-burndown.yml` — runner image updated to `ob-18f0014`

Updated all container `image:` references from `ob-77dfdfa` to `ob-18f0014`. The
previous image's baked binary passed `ContextManagement={type:"compaction"}` in
`ResponseNewParams` to OpenAI's Responses API, which rejects it with
`400 "Unsupported context_management type: ''."` — every `dispatch-one` call
failed at iter 1. Fixed upstream in `falkcorp/overnight-burndown#62`; new image
baked from `overnight-burndown@18f0014` (falkcorp/burndown-runner-image#23).

#### `reusable-burndown.yml` — declare `JF_CI_GH_PAT` in `workflow_call` secrets (v1.11.1)

`secrets.JF_CI_GH_PAT` was referenced in 4 container `credentials.password`
blocks but never declared in `on.workflow_call.secrets`. GitHub validates
reusable workflow secrets at parse time; any caller failed immediately with
"workflow file issue". Added `JF_CI_GH_PAT: required: false`. (PR #305)

## [v1.11.0] — 2026-06-09

### Added

#### `reusable-burndown.yml` — `rebase-stale` job for automatic PR conflict resolution

New `rebase-stale` job runs in parallel with `preflight` at the start of every
burndown run. It finds all open `automation`-labeled PRs where GitHub reports
`mergeable == CONFLICTING`, rebases each onto `main`, and force-pushes:

- Clean rebase → force-push, remove `status:conflict-unresolvable` label if
  present
- Conflict → `git rebase --abort`, add `status:conflict-unresolvable` label,
  post comment: "close and re-dispatch to regenerate from current `main`"
- `triage` now `needs: [preflight, rebase-stale]` so dispatch always starts from
  a post-rebase base
- `continue-on-error: true` on the rebase step: git errors never block new
  dispatch

New label created automatically: `status:conflict-unresolvable` (`#b60205` red).

README rewritten to be concise (removed duplicated bloat, moved detail to
CHANGELOG).

## [v1.10.0] — 2026-06-02

### Added

- `max_tasks` input to cap dispatched tasks per run (prevents OpenAI 429 on
  large queues)
- Scheduled runs in calling repos now use `full` mode (auto-merge) via
  caller-side condition

## [v1.9.0] — (prior)

### Completed

#### January 10, 2026 - Docker Rollout Across Action Repositories

- Completed Docker support for 11/18 action repositories representing all
  actions where Docker adds clear value
- Dockerized actions: detect-languages-action, load-config-action,
  get-frontend-config-action, package-assets-action,
  ci-generate-matrices-action, auto-module-tagging-action,
  generate-version-action, release-docker-action, release-frontend-action,
  release-go-action, release-protobuf-action
- Each dockerized action includes:
  - Dockerfile with pinned base image by digest
  - .dockerignore for build optimization
  - publish-docker.yml workflow for GHCR publishing with auto-versioning
  - use-docker/docker-image inputs with docker/host execution branching
  - Updated README, CHANGELOG, TODO with Docker usage instructions
- Intentionally skipped Docker for 7 actions:
  - Release orchestrators (release-python-action, release-rust-action): Require
    GitHub Actions ecosystem (setup-python, setup-rust) and external service
    publishing
  - Embedded Python actions (ci-workflow-helpers-action, pr-auto-label-action,
    docs-generator-action, security-summary-action, release-strategy-action):
    Use shell: python with code embedded in action.yml; Docker support would
    require significant refactoring for marginal benefit

### In Progress

(No active Docker rollout work - 11/18 suitable actions completed)

### Security

#### January 2, 2026 - Action Security Hardening

- Pinned all external GitHub Actions to full-length commit SHAs across 9 action
  repositories
- Updated action format to `owner/action@FULL_SHA # vX.Y.Z` for security +
  dependabot compatibility
- Audited and fetched latest versions for 15 external action dependencies:
  - GitHub official actions: checkout v6.0.1, setup-go v5.6.0, setup-node
    v6.1.0, setup-python v6.1.0, upload-artifact v6.0.0
  - Third-party actions: yamllint v3.1.1, gh-release v2.5.0, rust-toolchain
    v1.15.2, goreleaser v6.4.0, buf-setup v1.50.0
  - Docker actions: login v3.6.0, setup-buildx v3.12.0, setup-qemu v3.7.0,
    build-push v6.18.0, metadata v5.10.0
- Updated 9 repos with pinned hashes: get-frontend-config-action,
  auto-module-tagging-action, load-config-action, release-docker-action,
  release-frontend-action, release-go-action, release-protobuf-action,
  release-python-action, release-rust-action
- Enabled "require actions to be pinned to full-length commit SHA" repository
  setting on 17 action repos via GitHub API
- Deployed pre-commit hooks configuration (.pre-commit-config.yaml) to all 17
  action repos
- Deployed linter configurations (.markdownlint.json, .prettierrc.json,
  ruff.toml) to all 17 action repos
- Tested pre-commit hooks in all 17 action repos to ensure clean execution
- Fixed pre-commit configuration issues across all repos:
  - Corrected yamllint config path from `.yaml-lint.yml` to `.yamllint`
  - Corrected ruff config path from `.github/linters/ruff.toml` to `ruff.toml`
    (root directory)
- Created `.yamllint` configuration files with standard rules (line-length: 120,
  disable document-start) in all 17 repos
- Committed linter auto-fixes from pre-commit testing (prettier and shfmt
  formatting improvements) across all repos
- Created missing TODO.md and CHANGELOG.md files in 14 action repos with proper
  metadata headers (file path, version, guid)
- All 18 action repositories now have complete documentation structure
- All changes committed and pushed individually per repository
- Ensures consistent code quality enforcement and security best practices across
  all action repositories

### Fixed

#### May 31, 2026 - Reusable Security CodeQL JavaScript build mode

- Fixed `reusable-security.yml` so JavaScript CodeQL uses `build-mode: none`,
  matching current CodeQL requirements.
- Kept Go CodeQL on `autobuild` and made the autobuild step conditional on the
  resolved per-language build mode.
- Mirrored the same per-language build-mode behavior in `ghcommon`'s own
  Security workflow.
- Verified by green `ghcommon` Security run `26727776233` and downstream
  `audiobook-organizer` Security run `26727789014`.

#### December 26, 2025 - CI npm caching hardening

- Added directory creation step to prevent "paths not resolved" warnings in npm
  cache
- Expanded cache paths from `~/.npm` to `["~/.npm", "~/.cache/npm"]` for full
  coverage
- Included Node version in cache keys (`${{ inputs.node-version }}` for
  workflow-scripts; `${{ matrix.node-version }}` for frontend-ci)
- Improved restore-key fallback chain for better cache hit rates across Node
  version changes
- Resolves TODO-012 (npm cache path resolution) and strengthens CRITICAL-002
  (manual caching strategy)

## 2025-10-30

### Added

- Shared workflow foundation utilities (`workflow_common.py`) with config
  validation schema, feature flags, and supporting tests.
- Reusable CI workflow stack (helper, reusable workflow, feature-flagged caller)
  plus unit/integration coverage for change detection and matrix generation.
- Branch-aware release helper and reusable release workflow with GitHub Packages
  documentation, publish helper, release summary generator, and unit tests.
- GitHub Packages publishing helper (`publish_to_github_packages.py`), reusable
  workflow job integration, new documentation, and unit tests.
- GitHub Packages publishing script (`publish_to_github_packages.py`), workflow
  integration, and unit tests.
- Repository configuration updates enabling new CI and release systems,
  including registry preferences for future package publishing.

### Changed

- Modernized CI and release workflows to rely on repository feature flags
  instead of legacy configuration.
- Removed deprecated `.github/workflow-config.yaml` in favor of the new
  schema-driven configuration.
