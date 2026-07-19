<!-- file: TODO.md -->
<!-- version: 2.3.5 -->
<!-- guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a -->
<!-- last-edited: 2026-07-19 -->

# TODO

## 📥 Inbox

Tasks assembled from `todo.d/` fragments. Add a new task by dropping a fragment
file in `todo.d/` rather than editing this section by hand — see
[`todo.d/README.md`](todo.d/README.md). Checking a task off, or promoting it
into one of the curated sections below, is a normal direct edit.

<!-- todo-insert-here -->

## ✅ Recently completed (June 10, 2026)

- [x] **BRN-PAT** Declare `JF_CI_GH_PAT` in `reusable-burndown.yml`
      `workflow_call` secrets — callers were failing with "workflow file issue"
      (PR #305)
- [x] **BRN-IMG** Update runner image to `ob-18f0014` — removes broken
      `ContextManagement` OpenAI param that caused every `dispatch-one` to fail
      with `400 "Unsupported context_management type: ''"` (PR #306, auto-merged
      by retag CI)

## 🤖 Background Agent Queue (manage_todo_list sync)

- [ ] Plan security workflow actionization - Goal: Move security scanning logic
      out of reusable-security.yml into auditable composite actions with
      external scripts only. - Scope (initial action repos): -
      jdfalk/security-codeql-action: Orchestrate codeql init/analyze/upload
      (wraps actions/codeql) with repo config overrides. -
      jdfalk/security-trivy-action: Trivy filesystem/image/vulnerability scan
      with SARIF output and severity gating. - jdfalk/security-osv-scan-action:
      OSV-Scanner on repo dependencies (Go, Python, Node, Rust) with SARIF
      output. - jdfalk/security-secrets-action: Gitleaks (or repo-level secret
      scan wrapper) with allowlist support. - jdfalk/security-summary-action:
      Aggregate SARIFs, gate on thresholds, and write step summary +
      artifacts. - Inputs/Outputs (common): - Inputs: `paths`, `exclude`,
      `severity-threshold`, `fail-on`, `sarif-path`, `upload-sarif`
      (true/false), `tool-args`. - Outputs: `sarif`, `findings-count`,
      `critical-count`, `high-count`, `failed`. - Deliverables: - Each repo:
      action.yml, README with usage, src/ implementation (Python/Bash),
      .github/workflows/ci.yml tests. - Tags: v1.0.0 initial, moving tags v1 and
      v1.0, GitHub Release with changelog. - Docs: ghcommon
      ACTIONS_INTEGRATION_GUIDE.md section for security actions + examples. -
      Acceptance Criteria: - Actions run on sample repos producing SARIF,
      respect thresholds, and publish summaries. - reusable-security.yml
      refactored to call these actions; dry-run passes in 2 representative
      repos. - Risks/Notes: Keep codeql on GH-hosted runners; avoid inline
      scripts; support matrix by language as needed.

- [ ] Audit remaining workflows for action conversion - Inventory Targets: -
      reusable-advanced-cache.yml → cache-strategy-action -
      reusable-maintenance.yml → maintenance-summary-action -
      reusable-protobuf.yml → protobuf-config-action, protobuf-verify-action (if
      not done) - documentation.yml → docs-generator-action -
      issue-automation.yml → intelligent-labeling-action - sync-receiver.yml →
      sync-receiver-action - Steps: - Build call graph from
      WORKFLOW_SCRIPT_USAGE_MAP.md to confirm dependencies. - Define action
      contracts (inputs/outputs) matching current scripts. - Draft action repos
      list, ownership, and rollout order (P1→P4). - Deliverables: Updated
      WORKFLOW_SCRIPT_AUDIT.md with status, risks, and ETA per action. -
      Acceptance Criteria: Signed-off actionization plan with sequencing and
      test strategy.

- [ ] Validate new composite actions CI/CD pipelines - Scope: Six
      already-created actions (load-config, ci-generate-matrices,
      detect-languages, release-strategy, generate-version, package-assets). -
      Tests to Run: - Lint/parse action.yml; run action unit tests via local
      workflow in each repo. - Integration: use minimal sample repos to execute
      typical paths and verify outputs + summaries. - Failure modes: missing
      configs, malformed inputs, matrix edge cases. - Observability: Ensure
      GITHUB_STEP_SUMMARY is populated and outputs match docs exactly. -
      Deliverables: ACTIONS_VERIFICATION_REPORT.md updated with run IDs and
      pass/fail notes. - Acceptance Criteria: All action repos have green CI on
      main and successful integration runs.

- [ ] Verify action tags and releases (v1/v1.0/v1.0.0) - Tag Policy: - Create
      immutable v1.0.0 tags; create/update moving tags v1 and v1.0 to latest
      compatible. - Ensure GitHub Releases exist for v1.0.0 with notes mirroring
      README features and changes. - Steps: - List tags in each action repo;
      create missing moving tags; verify protection settings. - Confirm release
      metadata: title, body, links to example workflows, and compatibility
      notes. - Deliverables: Tag and Release checklist log per repo in ghcommon
      (logs/tags/...). - Acceptance Criteria: Consumers can pin @v1, @v1.0, or
      @v1.0.0 consistently; Marketplace visibility OK.

- [ ] Update reusable workflows to use new actions and verify - Targets:
      reusable-ci.yml (partially done), reusable-release.yml (partially done),
      reusable-security.yml (new), protobuf workflow (if applicable). - Steps: -
      Replace inline/scripted steps with uses: jdfalk/\*-action@v1. - Keep
      dorny/paths-filter where fit; remove sparse-checkout logic entirely. - Add
      summary checkpoints and robust outputs wiring between jobs. - Run on
      ghcommon (self) and audiobook-organizer as canary; capture run logs. -
      Deliverables: PR/commit diffs for each workflow; Integration Guide updated
      with before/after. - Acceptance Criteria: Green pipeline in canary repos;
      artifacts/releases intact; no inline scripts remain.

- [x] Roll out dockerized action paths + GHCR auto-publish workflows across
      suitable action repos. Status: COMPLETED (11/18 suitable repos).
      Dockerized: detect-languages-action, load-config-action,
      get-frontend-config-action, package-assets-action,
      ci-generate-matrices-action, auto-module-tagging-action,
      generate-version-action, release-docker-action, release-frontend-action,
      release-go-action, release-protobuf-action. Intentionally skipped 7
      actions: 2 release orchestrators (release-python-action,
      release-rust-action) require GitHub Actions ecosystem and external
      services; 5 embedded Python actions (ci-workflow-helpers-action,
      pr-auto-label-action, docs-generator-action, security-summary-action,
      release-strategy-action) would require significant refactoring for
      marginal benefit. Deliverables achieved: Dockerfile/.dockerignore,
      `use-docker`/`docker-image` inputs with docker/host branching,
      README/CHANGELOG/TODO updates, publish-docker workflow that builds/pushes
      GHCR, updates pinned digest in action.yml, commits and tags.

### Standardize Action Repo Workflows (ci.yml, release.yml, integration)

- ✅ COMPLETED (January 2, 2026)
- Scope: Every action repo gets consistent CI (lint + parse + minimal run),
  Release (tag + moving tags), and Integration (use action from tag in a sample
  run).
- Steps: - Add `ci.yml` with actionlint, yamllint, markdownlint,
  shellcheck/pyflakes as applicable; run an example job `uses: ./` and assert
  outputs. - Add `release.yml` to create vX.Y.Z, update vX and vX.Y, generate
  GitHub Release notes, attach example snippets. - Add `test-integration.yml` to
  `uses: owner/repo@v1` ensuring public consumption works.
- Deliverables: Workflow files across all action repos; status badges in README.
- Acceptance: All actions show green CI for push/PR; release workflow produces
  tags/releases.
- Completion Notes:
  - All 18 action repos have auto-merge.yml
  - 242 labels synced across all repos using sync-labels-fast.py
  - All repos have dependabot.yml configured
  - Created new point releases: 14 repos at v1.1.2, 4 repos at v1.0.1
  - Force-updated floating tags (v1, v1.0) to latest commits across all repos

### Security Hardening for Workflows

- ✅ COMPLETED (January 2, 2026)
- Scope: Apply least-privilege permissions, pin actions to SHAs or major
  versions, add security scanning.
- Steps: - Set `permissions` per job; default to `read` and escalate only when
  needed (contents, id-token, attestations, etc.). - Pin third-party actions
  (actionlint suggests), enable OIDC for publishing when applicable. - Add
  CodeQL or basic SAST for helper code; add Trivy for containers where relevant.
- Deliverables: Updated workflows with pinned actions, permissions, security
  checks documented.
- Progress:
  - ✅ Audited all external action dependencies across 18 repos
  - ✅ Fetched latest releases and commit SHAs for 15 external actions
  - ✅ Pinned all external actions to format: owner/action@FULL_SHA # vX.Y.Z
  - ✅ Updated 9 action repos with pinned hashes and pushed changes
  - ✅ Enabled "require SHA pinning" setting on 17 action repos via GitHub API
  - ✅ Deployed pre-commit hooks and linter configs to all 17 action repos
  - ✅ Tested pre-commit hooks in all 17 repos to verify clean execution
  - ✅ Fixed pre-commit config issues (yamllint and ruff paths) across all repos
  - ✅ Created .yamllint configuration files with standard rules in all repos
  - ✅ Committed linter auto-fixes (prettier, shfmt formatting) from pre-commit
    testing
  - ✅ Ensured all 18 repos have TODO.md and CHANGELOG.md with proper headers
    and templates
  - ✅ Fixed reusable Security CodeQL build-mode mapping so JavaScript uses
    `build-mode: none`; verified in `ghcommon` run `26727776233` and
    `audiobook-organizer` run `26727789014`
- Acceptance: No `warning: write-all` permissions; Dependabot alerts addressed
  for action pins.

### Documentation Completeness (READMEs, Inputs/Outputs, Examples)

- Scope: Ensure each action README includes inputs/outputs tables, examples for
  common and advanced usage, and links to reusable workflow examples.
- Steps: - Generate Inputs/Outputs from action.yml to markdown tables; add
  minimal and advanced examples. - Add badges: CI, Release, Marketplace (if
  applicable), Version tags. - Cross-link to ghcommon Integration Guide
  sections.
- Deliverables: Updated READMEs across all actions; docs PR linking strategy.
- Acceptance: Lint passes (markdownlint), and examples verified via integration
  workflow.

### End-to-End Validation in Example Consumer Repo(s)

- Scope: Create/refresh a small sample repo that consumes reusable-ci and
  reusable-release, and exercises new actions in realistic paths (Go, Python,
  Frontend variants).
- Steps: - Matrix run: Linux primary; optionally macOS/Windows smoke checks for
  action portability. - Trigger CI and Release flows; verify artifacts, tags,
  releases, and summaries. - Capture run IDs and logs; add to Verification
  Report.
- Deliverables: `example-consumer` results logged and referenced; issues filed
  for any regressions.
- Acceptance: Green end-to-end runs with artifacts/releases matching
  expectations.

### Backward Compatibility & Deprecation Plan

- Scope: Provide a safe migration off scripts to actions without breaking
  existing callers.
- Steps: - Keep current workflows working; introduce new action-powered paths
  under a feature flag window. - Emit warnings in summaries when legacy script
  path executed; set removal timeline. - Document migration steps and timelines
  in ghcommon.
- Deliverables: Deprecation notice, migration guide, feature flag defaults
  schedule.
- Acceptance: No hard breaks during migration window; consumers adopt new
  actions successfully.

### Governance & Protections

- Scope: Ensure changes to workflows/actions require appropriate review and pass
  required checks.
- Steps: - Update CODEOWNERS for `.github/workflows/**` and action repos; set
  required checks for merges. - Enforce branch protection rules and conventional
  commit checks. - Add PR templates for action repos with checklist (docs, tags,
  tests).
- Deliverables: Governance config updates across repos.
- Acceptance: Merges to main blocked without reviews + green checks; history
  clean via conventions.

### Org-wide Monitoring & Summaries

- Scope: Central visibility of runs, failures, tag creation, and adoption rate.
- Steps: - Extend workflow-debugger to include action repo CI health and
  tag/release verification. - Nightly job to aggregate status across repos and
  post summary artifact. - Track adoption of new actions by repository and
  workflow.
- Deliverables: Monitoring scripts/workflows and summary artifacts.
- Acceptance: Weekly status reports show CI health and adoption metrics.

## ✅ Completed

- [x] Phase 0: Shared workflow foundations (`workflow_common.py`, config schema,
      validation tooling, security checklist, core tests)
- [x] Phase 1: CI modernization (change detection helper, reusable CI workflow,
      feature-flagged caller, unit + integration tests)
- [x] Phase 2: Release consolidation (branch-aware release helper, reusable
      release workflow, feature-flagged caller, GitHub Packages docs/tests)
- [x] GitHub Packages publishing job, helper script, rollout docs, automated
      tests, and summary tooling

## 🚧 In Progress / Upcoming

### Phase 3: Documentation Automation

- [x] Build doc-change detection pipeline and reusable documentation workflow
- [x] Implement auto-generated docs publishing and changelog updates
- [x] Wire feature flag `use_new_docs` into workflows and repository
      configuration
- [x] Add unit/integration tests for doc automation helpers and workflows

### Phase 4: Maintenance Automation

- [x] Implement maintenance helpers for dependency updates (docs + summary
      tooling).
- [x] Create reusable maintenance workflow and feature-flagged caller (wired to
      maintenance helper)
- [x] Add scheduling + configuration hooks for maintenance jobs across repos
      (config-driven via repository-config.yml)
- [x] Document maintenance automation runbooks and verification steps

### Phase 5: Advanced Features

- [x] Add metrics/observability helpers and analytics integration
- [x] Implement automation workflows for caching, analytics, and self-healing
      reporting
- [x] Extend workflow catalog/reference docs with advanced feature details

### Operations & Reference Tasks

- [x] Finalize rollback procedures, troubleshooting, and migration playbooks for
      v2 workflows
- [x] Update implementation guides (testing, release, CI) with new patterns and
      linters
- [x] Ensure helper scripts API reference reflects new modules and features
- [x] Validate workflow catalog entries for new reusable workflows (CI, release,
      docs, maintenance, advanced)

## 🔥 Critical - Action Repository CI Failures

### Priority 1: Critical Failures (Missing Core Files)

#### #todo release-docker-action - Create Missing Files

**Status:** Blocked **Priority:** Critical **Repository:**
[release-docker-action](https://github.com/jdfalk/release-docker-action)

**Issues:**

- Missing action.yml completely
- Missing README.md
- Missing test Dockerfile
- Tests failing due to missing files

**Action Items:**

1. Create action.yml with complete action definition
2. Create README.md with usage documentation
3. Create test structure with sample Dockerfile
4. Implement Docker build functionality
5. Fix and test CI workflow

**Tracking:** See
`/Users/jdfalk/repos/github.com/jdfalk/release-docker-action/TODO.md`

---

#### #todo release-go-action - Create Missing Files

**Status:** Blocked **Priority:** Critical **Repository:**
[release-go-action](https://github.com/jdfalk/release-go-action)

**Issues:**

- Missing action.yml completely
- Missing README.md
- No action implementation

**Action Items:**

1. Create action.yml with Go build configuration
2. Create README.md with usage documentation
3. Implement cross-compilation support
4. Add release artifact handling
5. Fix and test CI workflow

**Tracking:** See
`/Users/jdfalk/repos/github.com/jdfalk/release-go-action/TODO.md`

---

### Priority 2: High Priority Failures (Lint/Config Issues)

#### #todo auto-module-tagging-action - Fix YAML Linting

**Status:** Open **Priority:** High **Repository:**
[auto-module-tagging-action](https://github.com/jdfalk/auto-module-tagging-action)

**Issues:**

- 10 YAML line length violations (lines too long)
- Test execution failing (exit code 128)
- Cache restore warnings

**Action Items:**

1. Fix all yamllint line length errors in action.yml
2. Investigate and fix test execution error (exit 128)
3. Fix Go module cache configuration
4. Test and verify CI passes

**Tracking:** See
`/Users/jdfalk/repos/github.com/jdfalk/auto-module-tagging-action/TODO.md`

---

#### #todo release-frontend-action - Fix YAML Linting

**Status:** Open **Priority:** High **Repository:**
[release-frontend-action](https://github.com/jdfalk/release-frontend-action)

**Issues:**

- 6 YAML line length violations
- Missing README.md
- Cache dependencies error

**Action Items:**

1. Fix all yamllint line length errors in action.yml
2. Create comprehensive README.md
3. Fix cache dependencies configuration
4. Test and verify CI passes

**Tracking:** See
`/Users/jdfalk/repos/github.com/jdfalk/release-frontend-action/TODO.md`

---

#### #todo release-rust-action - Fix Cargo.toml Error

**Status:** Open **Priority:** High **Repository:**
[release-rust-action](https://github.com/jdfalk/release-rust-action)

**Issues:**

- rust-cache action cannot find Cargo.toml
- Incorrectly treating composite action repo as Rust project
- Test workflow needs restructuring

**Action Items:**

1. Remove or conditionally skip rust-cache in CI
2. Restructure test workflow for composite action testing
3. Create sample Rust project for integration testing
4. Test and verify CI passes

**Tracking:** See
`/Users/jdfalk/repos/github.com/jdfalk/release-rust-action/TODO.md`

---

### Priority 3: Working (No Immediate Action Required)

#### #todo release-protobuf-action - Monitor

**Status:** Passing **Priority:** Low **Repository:**
[release-protobuf-action](https://github.com/jdfalk/release-protobuf-action)

**Notes:**

- CI currently passing
- No failures detected
- Ready for migration to reusable workflows

**Tracking:** See
`/Users/jdfalk/repos/github.com/jdfalk/release-protobuf-action/TODO.md`

---

## 🔄 Migration to Reusable Workflows

### #todo Phase 1: Fix All CI Failures First

**Status:** In Progress **Priority:** Critical **Dependencies:** All above CI
fixes must be completed

**Completion Criteria:**

- [ ] release-docker-action: CI passing
- [ ] release-go-action: CI passing
- [ ] auto-module-tagging-action: CI passing
- [ ] release-frontend-action: CI passing
- [ ] release-rust-action: CI passing
- [ ] release-protobuf-action: CI verified passing

---

### #todo Phase 2: Migrate to Reusable Workflows

**Status:** Blocked **Priority:** High **Dependencies:** Phase 1 must complete
first

**Action Items:**

1. Update each action to use `.github/workflows/reusable-action-ci.yml`
2. Update each action to use `.github/workflows/reusable-release.yml`
3. Test workflows in each repository
4. Pull and verify logs for each workflow run
5. Document any issues or customizations needed

**Repositories to Migrate:**

- [ ] release-docker-action
- [ ] release-go-action
- [ ] auto-module-tagging-action
- [ ] release-frontend-action
- [ ] release-rust-action
- [ ] release-protobuf-action

---

### #todo Phase 3: Continuous Testing and Validation

**Status:** Blocked **Priority:** High **Dependencies:** Phase 2 must complete
first

**Testing Plan:**

1. Run CI workflows in each repository
2. Pull and analyze logs from each run
3. Verify all jobs pass successfully
4. Test release workflows with version bumps
5. Verify artifact creation and uploads
6. Document any issues found
7. Iterate until all workflows are stable

**Success Metrics:**

- All CI workflows passing
- All release workflows creating proper artifacts
- Logs showing no errors or warnings
- Documentation updated with any learnings

---

## 📊 Summary Status

**Total Repositories:** 6 **Critical Failures:** 2 (release-docker-action,
release-go-action) **High Priority Failures:** 3 (auto-module-tagging-action,
release-frontend-action, release-rust-action) **Passing:** 1
(release-protobuf-action)

**Estimated Timeline:**

- Phase 1 (Fix CI): 2-3 days
- Phase 2 (Migration): 1-2 days
- Phase 3 (Testing): 1-2 days
- **Total:** 4-7 days

---

**Last Updated:** 2025-12-19 **Next Review:** After critical failures are
resolved

---

## 🚀 High Priority: Action Repository Standardization (6 Items)

### #todo 1. Add auto-merge.yml to all action repos

**Status:** ✅ COMPLETED **Priority:** High **Workspace Folders:** All action
repos

**Context:** The auto-merge.yml workflow from get-frontend-config-action is
useful for automating PR merges with specific labels. Need to standardize this
across all action repositories.

**Action Repos to Update:**

- [x] detect-languages-action
- [x] generate-version-action
- [x] get-frontend-config-action (already has it)
- [x] package-assets-action
- [x] auto-module-tagging-action
- [x] ci-generate-matrices-action
- [x] load-config-action
- [x] release-docker-action
- [x] release-frontend-action
- [x] release-go-action
- [x] release-protobuf-action
- [x] release-python-action
- [x] release-rust-action
- [x] ci-workflow-helpers-action
- [x] pr-auto-label-action
- [x] docs-generator-action
- [x] release-strategy-action

**Action Items:**

1. [x] Copy `.github/workflows/auto-merge.yml` to all action repos
2. [x] Verify workflow triggers correctly on label addition
3. [x] Test with a sample PR using auto-merge label

**Completion Notes:**

- All 18 action repos verified to have auto-merge.yml
- Tags created and pushed: 18 repos with new point releases (v1.1.2 or v1.0.1)
- Floating tags (v1, v1.0) force-updated to latest commits

**File Reference:** [#file:auto-merge.yml]

---

### #todo 2. Sync labels to all action repos

**Status:** ✅ COMPLETED **Priority:** High **Script:** sync-labels-fast.py

**Context:** All repos should have consistent labels including dependabot
labels. The ghcommon repository has labels.json and sync-github-labels.py
script.

**Action Items:**

1. [x] Verify labels.json is up-to-date in ghcommon
2. [x] Run `python3 scripts/sync-labels-fast.py` for all 18 action repos
3. [x] Add GitHub-Actions, dependencies, github-actions labels if missing
4. [x] Verify all repos have color-coded labels
5. [x] Document label sync results

**Completion Notes:**

- Created new sync-labels-fast.py using `gh` CLI for 10x performance improvement
- Successfully synced 242 labels to all 18 action repos in ~10 seconds
- All repos now have consistent labeling across github-actions, dependencies,
  and custom labels

**Script Reference:**
`/Users/jdfalk/repos/github.com/falkcorp/github-common/scripts/sync-labels-fast.py`

**Labels File:**
`/Users/jdfalk/repos/github.com/falkcorp/github-common/labels.json`

---

### #todo 3. Add dependabot.yml to all action repos

**Status:** ✅ COMPLETED **Priority:** High **Template File:**
[#file:dependabot.yml]

**Context:** All action repos need dependabot configuration to keep dependencies
updated with proper labels and commit messages.

**Action Repos to Update:** Same as #todo 1

**Action Items:**

1. [x] Copy `.github/dependabot.yml` to all action repos from template
2. [x] Verify configuration includes:
   - github-actions ecosystem
   - Weekly schedule (Wednesday 10:00 AM)
   - auto-merge and dependencies labels
   - ci prefix for commit messages
3. [x] Test dependabot triggers on a repo

**Completion Notes:**

- Added dependabot.yml to 5 missing repos (auto-module-tagging-action,
  ci-workflow-helpers-action, docs-generator-action, get-frontend-config-action,
  pr-auto-label-action)
- All 18 action repos now have consistent dependabot configuration
- Tags created and pushed with new point releases for each repo

**Template Reference:** [#file:dependabot.yml] in generate-version-action

---

### #todo 4. Standardize CI workflows across action repos

**Status:** Not Started **Priority:** High **Templates:** test-action.yml,
ci.yml (release-rust-action, release-frontend-action)

**Context:** Some repos have test-action.yml, others have ci.yml. Need to
consolidate to a single standard that supports both common tests and
repository-specific tests via repository-config.yml.

**Current State:**

- get-frontend-config-action: test-action.yml
- release-rust-action: ci.yml (with Rust-specific setup)
- release-frontend-action: ci.yml (with Node-specific setup)
- Others: Vary

**Action Items:**

1. [ ] Review all existing CI workflows in action repos
2. [ ] Design unified ci.yml template supporting:
   - action.yml validation
   - README validation
   - Language-specific setup hooks (go, node, rust, python)
   - Repository-config.yml integration for additional tests
   - Example action execution test
3. [ ] Create ci.yml template in ghcommon
4. [ ] Deploy to all action repos
5. [ ] Verify all CI workflows pass

**Key Requirements:**

- Lint action.yml with actionlint
- Validate README.md exists
- Run language-specific tests if applicable
- Execute action with sample inputs
- Must be repeatable across diverse action types

---

### #todo 5. Add release.yml to all action repos

**Status:** Not Started **Priority:** High **Templates:** [#file:release.yml]
(release-rust-action), [#file:release.yml] (release-frontend-action)

**Context:** All action repos need intelligent release workflows that create
semantic version tags, moving tags (v1, v1.0), and GitHub releases.

**Action Repos to Update:** Same as #todo 1

**Action Items:**

1. [ ] Review existing release.yml from release-rust-action and
       release-frontend-action
2. [ ] Create unified release.yml template supporting:
   - Trigger on version tags (v*.*.\*)
   - Manual workflow_dispatch with version input
   - Generate changelog from previous tag
   - Create GitHub Release with generated changelog
   - Update major.minor moving tags (v1 → v1.0 → v1.0.0)
   - Proper permissions (contents: write)
3. [ ] Deploy to all action repos
4. [ ] Test release workflow with sample version

**Template Reference:** [#file:release.yml] in release-rust-action and
release-frontend-action

**Key Requirements:**

- Determine version from tag or workflow_dispatch input
- Generate changelog between tags
- Create GitHub Release
- Update moving tags automatically

---

### #todo 6. Find and run repo settings script

**Status:** Research Phase **Priority:** High **Scripts:** sync-repo-setup.py,
others

**Context:** ghcommon should have a script to synchronize repository settings
(rebase-only merges, auto-delete branches, etc.) across repos. Need to find and
understand this script.

**Action Items:**

1. [ ] Locate the repo settings/sync script in ghcommon
2. [ ] Review script to understand:
   - What settings it modifies
   - How to configure target repos
   - Any prerequisites or dependencies
3. [ ] Document the settings it applies:
   - Rebase-only merge strategy
   - Auto-delete head branches on merge
   - Require status checks to pass
   - Require branches to be up to date before merging
   - Dismiss stale reviews on new pushes
4. [ ] Run script against all action repos
5. [ ] Verify settings are applied correctly

**Script Search Results:**

- `sync-repo-setup.py` - Likely candidate for instructions/config sync
- `sync-github-labels.py` - Used for label sync
- Various sync-\*.py scripts in `.github/scripts/`

**Expected Findings:**

- Script should handle repository setup including merge strategy
- May use GitHub API for repository settings
- Should be idempotent (safe to run multiple times)

---

## 🚀 New High Priority Tasks

### #todo Tag release-go-action as v2.0.0

**Status:** Ready **Priority:** Critical **Repository:**
[release-go-action](https://github.com/jdfalk/release-go-action)

**Context:** release-go-action has been completely rewritten to use GoReleaser
instead of manual Go builds. This is a breaking change requiring v2.0.0.

**Action Items:**

1. [ ] Ensure release-go-action changes are committed and pushed
2. [ ] Run `scripts/tag-release-go-v2.sh` to create v2.0.0, v2.0, and v2 tags
3. [ ] Verify tags are pushed to GitHub
4. [ ] Get commit hash for pinning in workflows
5. [ ] Update ghcommon workflows to use v2

**Script:**
`/Users/jdfalk/repos/github.com/falkcorp/github-common/scripts/tag-release-go-v2.sh`

---

### #todo Pin all actions to commit hashes

**Status:** Ready **Priority:** High **Repository:** ghcommon

**Context:** All jdfalk/\* actions should be pinned to specific commit hashes
with version comments for security and reproducibility.

**Action Items:**

1. [ ] Run `scripts/pin-actions-to-hashes.py` to discover and pin actions
2. [ ] Review generated ACTION_VERSIONS.md reference file
3. [ ] Verify all workflows use `jdfalk/action@hash # vX.Y.Z` format
4. [ ] Commit and push changes
5. [ ] Update documentation with pinning policy

**Script:**
`/Users/jdfalk/repos/github.com/falkcorp/github-common/scripts/pin-actions-to-hashes.py`

**Output:** `ACTION_VERSIONS.md` - Version/hash reference table

---

### #todo Convert reusable workflows to new actions

**Status:** Pending **Priority:** High **Repository:** ghcommon

**Context:** Now that actions are extracted, convert reusable workflows to use
the new jdfalk/\* actions.

**Action Items:**

1. [ ] Update `release-go.yml` to use `falkcorp/gha-release-go@hash # v2.0.1`
2. [ ] Update `release-docker.yml` to use
       `falkcorp/gha-release-docker@hash # v1.0.0`
3. [ ] Update `release-frontend.yml` to use
       `falkcorp/gha-release-frontend@hash # v1.0.0`
4. [ ] Update `release-python.yml` to use
       `falkcorp/gha-release-python@hash # v1.0.0`
5. [ ] Update `release-rust.yml` to use
       `falkcorp/gha-release-rust@hash # v1.0.0`
6. [ ] Update `release-protobuf.yml` to use
       `falkcorp/gha-release-protobuf-base@hash # v1.0.0`
7. [ ] Test each workflow conversion
8. [ ] Document migration for repositories using these workflows

**Dependencies:** Requires #todo Pin all actions to commit hashes

---

### #todo Monitor and fix remaining action CI failures

**Status:** In Progress **Priority:** High **Repository:** All action repos

**Context:** Some actions still have CI failures that need investigation and
fixing.

**Action Items:**

1. [ ] Run `scripts/trigger-and-monitor-ci.sh` to check all action CI status
2. [ ] Review failure logs in `logs/ci-failures/`
3. [ ] Fix any remaining YAML linting errors
4. [ ] Fix any test failures
5. [ ] Ensure all actions pass CI before v1.0.0 release

**Completed:**

- ✅ Fixed action.yml shell parameter errors
- ✅ Fixed input validation mismatches
- ✅ Added GoReleaser support to release-go-action (v2.0.0)

---

## Action Repo Standardization (2025-01-01)

### 1. Add auto-merge workflow to all action repos

**Status:** ✅ Completed **Priority:** High

Copy `auto-merge.yml` from `get-frontend-config-action` to all action repos with
`action` in the name.

**Completed:**

- ✅ All 16 main action repos have auto-merge.yml
- ✅ Added to: detect-languages-action, generate-version-action,
  package-assets-action, auto-module-tagging-action,
  ci-generate-matrices-action, load-config-action, release-docker-action,
  release-frontend-action, release-go-action, release-protobuf-action,
  release-python-action, release-rust-action, ci-workflow-helpers-action,
  pr-auto-label-action, docs-generator-action, release-strategy-action,
  security-summary-action

---

### 2. Ensure all action repos have complete labels and dependabot config

**Status:** Not Started **Priority:** High

Sync labels from ghcommon to all action repos, and ensure dependabot.yml is in
each.

**Action Items:**

1. [ ] Check `scripts/sync-labels-to-action-repos.py` in ghcommon for label list
2. [ ] Run label sync script for all action repos
3. [ ] Add `.github/dependabot.yml` to each action repo (github-actions updates)
4. [ ] Commit and push to each repo
5. [ ] Tag each repo and update floating tags

**Script Location:** `ghcommon/scripts/sync-labels-to-action-repos.py`

---

### 3. Ensure all action repos have dependabot.yml

**Status:** Not Started **Priority:** High

Verify and add `.github/dependabot.yml` to all action repos for automated
dependency updates.

**Action Items:**

1. [ ] Check which repos are missing `dependabot.yml`
2. [ ] Create/copy dependabot.yml to repos that don't have it
3. [ ] Ensure it includes `github-actions` package ecosystem
4. [ ] Commit and push to each repo
5. [ ] Tag each repo and update floating tags

**Template:** Based on `generate-version-action/.github/dependabot.yml`

---

### 4. Standardize CI workflows across action repos

**Status:** Not Started **Priority:** High

Consolidate different CI workflows (test-action.yml, ci.yml) into a unified
pattern that supports action-specific tests via repository config.

**Action Items:**

1. [ ] Review all existing CI workflows in action repos
2. [ ] Create standard `ci.yml` template with:
   - Validate action.yml
   - Lint (yamllint, markdownlint)
   - Test action execution (basic `uses: ./`)
   - Allow for repo-specific additional tests
3. [ ] Apply to all action repos
4. [ ] Commit and push to each repo
5. [ ] Tag each repo and update floating tags

**Template Base:** `release-rust-action/.github/workflows/ci.yml` and
`release-frontend-action/.github/workflows/ci.yml`

---

### 5. Ensure all action repos have release.yml workflow

**Status:** Not Started **Priority:** High

Implement consistent release workflow with version detection, changelog
generation, tag management, and floating tag updates.

**Action Items:**

1. [ ] Review release.yml in release-rust-action and release-frontend-action
2. [ ] Create standardized `release.yml` template
3. [ ] Apply to all action repos that don't have it
4. [ ] Commit and push to each repo
5. [ ] Tag each repo and update floating tags

**Template Base:** `release-rust-action/.github/workflows/release.yml` and
`release-frontend-action/.github/workflows/release.yml`

---

### 6. Apply common repository settings to all action repos

**Status:** Not Started **Priority:** High

Use repository settings script to apply consistent configuration across all
action repos (rebase-only merges, branch protection, etc).

**Action Items:**

1. [ ] Find and review repository settings script in ghcommon
2. [ ] Document all configured settings and their values
3. [ ] Run script against all action repos to validate/update settings
4. [ ] Verify settings are applied correctly in each repo via GitHub web UI
5. [ ] Document results

**Expected Settings:**

- Rebase-only merges enabled
- Branch protection on main
- Require PR reviews (if configured)
- Require status checks to pass
- Other standard settings from ghcommon

---
