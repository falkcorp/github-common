<!-- file: WORKFLOW_SCRIPT_USAGE_MAP.md -->
<!-- version: 1.0.1 -->
<!-- guid: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e -->
<!-- last-edited: 2026-10-16 -->

# Workflow Script Usage Mapping

**Date:** December 20, 2025 **Purpose:** Detailed call graph of script
dependencies across workflows **Status:** Phase 2 - Workflow Mapping Complete

## Mapping Methodology

This document maps **every script call** in the ghcommon workflow files to
understand:

1. Which workflows depend on which scripts
2. How scripts are invoked (direct python call, shell wrapper, etc.)
3. What environment variables are required
4. What outputs are produced

---

## Critical Path: Config Loading Pattern

**Every reusable workflow follows this pattern:**

```yaml
# Step 1: Detect ghcommon ref (which version to use)
- name: Get ghcommon workflow ref
  id: ghcommon-ref
  run: |
    ref="${GITHUB_WORKFLOW_REF##*@}"
    if [[ -z "$ref" || "$ref" == "$GITHUB_WORKFLOW_REF" ]]; then
      ref="refs/heads/main"
    fi
    echo "ref=$ref" >> "$GITHUB_OUTPUT"

# Step 2: Sparse checkout of scripts directory
- name: Checkout ghcommon workflow scripts
  uses: actions/checkout@v6
  with:
    repository: jdfalk/ghcommon
    ref: ${{ steps.ghcommon-ref.outputs.ref }}
    path: ghcommon-workflow-scripts # or .ghcommon
    sparse-checkout: |
      .github/workflows/scripts
    sparse-checkout-cone-mode: false

# Step 3: Set GHCOMMON_SCRIPTS_DIR environment variable
- name: Configure workflow script path
  run: |
    echo "GHCOMMON_SCRIPTS_DIR=$PWD/ghcommon-workflow-scripts/.github/workflows/scripts" >> "$GITHUB_ENV"

# Step 4: Call scripts using $GHCOMMON_SCRIPTS_DIR
- name: Load configuration
  run: python3 "$GHCOMMON_SCRIPTS_DIR/load_repository_config.py"
```

**❌ Problem:** When called from external repos, the sparse checkout sometimes
fails or the path resolution breaks.

**✅ Solution:** Replace with action calls:

```yaml
- uses: falkcorp/gha-load-config@v1
  id: config
  with:
    config-file: .github/repository-config.yml
```

---

## Workflow #1: reusable-ci.yml (730 lines)

**Purpose:** Unified CI workflow for all languages **Usage:** Called by ALL
repositories for continuous integration **Script Dependencies:** HIGH (3
scripts)

### Script Call Mapping

#### Call #1: load_repository_config.py

**Location:** Job `load-config`, Step "Load repository configuration"

```yaml
- name: Load repository configuration
  id: load
  env:
    CONFIG_FILE: .github/repository-config.yml
  run: python3 "$GHCOMMON_SCRIPTS_DIR/load_repository_config.py"
```

**Inputs (Environment):**

- `CONFIG_FILE` - Path to repository-config.yml

**Outputs:**

- `config` - JSON string of config
- `has-config` - Boolean flag

**Conversion Target:** `falkcorp/gha-load-config@v1`

---

#### Call #2: ci_workflow.py generate-matrices

**Location:** Job `load-config`, Step "Generate language matrices"

```yaml
- name: Generate language matrices
  id: matrices
  env:
    REPOSITORY_CONFIG: ${{ steps.load.outputs.config }}
    FALLBACK_GO_VERSION: ${{ inputs.go-version }}
    FALLBACK_PYTHON_VERSION: ${{ inputs.python-version }}
    FALLBACK_RUST_VERSION: ${{ inputs.rust-version }}
    FALLBACK_NODE_VERSION: ${{ inputs.node-version }}
    FALLBACK_COVERAGE_THRESHOLD: ${{ inputs.coverage-threshold }}
  run: python3 "$GHCOMMON_SCRIPTS_DIR/ci_workflow.py" generate-matrices
```

**Inputs (Environment):**

- `REPOSITORY_CONFIG` - JSON config from previous step
- `FALLBACK_*_VERSION` - Default versions for each language
- `FALLBACK_COVERAGE_THRESHOLD` - Coverage threshold %

**Outputs:**

- `go-matrix` - JSON matrix of Go versions/OSes
- `python-matrix` - JSON matrix of Python versions/OSes
- `rust-matrix` - JSON matrix of Rust versions/OSes
- `frontend-matrix` - JSON matrix of Node versions/OSes
- `coverage-threshold` - Effective coverage threshold

**Dependencies:**

- `workflow_common.py` (for write_output)
- `load_repository_config.py` (indirect via REPOSITORY_CONFIG)

**Conversion Target:** `falkcorp/gha-ci-generate-matrices@v1`

---

#### Call #3: ci_workflow.py run-linters

**Location:** Job `super-linter`, Step "Run linters" (line ~400+)

```yaml
- name: Run Super Linter
  env:
    REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
    VALIDATE_ALL_CODEBASE: ${{ github.event_name != 'pull_request' }}
    DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}
  run: python3 "$GHCOMMON_SCRIPTS_DIR/ci_workflow.py" run-linters
```

**Inputs (Environment):**

- `REPOSITORY_CONFIG` - JSON config
- `VALIDATE_ALL_CODEBASE` - Boolean flag
- `DEFAULT_BRANCH` - Repository default branch

**Outputs:**

- Linter results via GITHUB_STEP_SUMMARY
- Exit code (0 = success, 1 = failures)

**Conversion Target:** `jdfalk/ci-run-linters-action@v1`

---

### Additional Dependencies (External Actions)

- `dorny/paths-filter@v3` - File change detection (NO script replacement needed)
- `github/super-linter@v4` - Linter execution (NO script replacement needed)

---

## Workflow #2: reusable-release.yml (591 lines)

**Purpose:** Orchestrate releases for all languages **Usage:** Called by
repositories on release tags **Script Dependencies:** CRITICAL (5+ scripts)

### Script Call Mapping

#### Call #1: load_repository_config.py

**Location:** Job `load-config`, Step "Load repository configuration"

```yaml
- name: Load repository configuration
  id: load-config
  env:
    CONFIG_FILE: .github/repository-config.yml
  run: python3 "$GHCOMMON_SCRIPTS_DIR/load_repository_config.py"
```

**Same as CI workflow** - See above.

**Conversion Target:** `falkcorp/gha-load-config@v1`

---

#### Call #2: release_workflow.py detect-languages

**Location:** Job `detect-languages`, Step "Detect project languages and
generate matrices"

```yaml
- name: Detect project languages and generate matrices
  id: detect
  env:
    REPOSITORY_CONFIG: ${{ needs.load-config.outputs.config }}
    SKIP_LANGUAGE_DETECTION: ${{ inputs.skip-language-detection }}
    BUILD_TARGET: ${{ inputs.build-target || 'all' }}
    GO_ENABLED: ${{ inputs.go-enabled && 'true' || 'auto' }}
    PYTHON_ENABLED: ${{ inputs.python-enabled && 'true' || 'auto' }}
    RUST_ENABLED: ${{ inputs.rust-enabled && 'true' || 'auto' }}
    FRONTEND_ENABLED: ${{ inputs.frontend-enabled && 'true' || 'auto' }}
    DOCKER_ENABLED: ${{ inputs.docker-enabled && 'true' || 'auto' }}
    PROTOBUF_ENABLED: ${{ inputs.protobuf-enabled && 'true' || 'auto' }}
  run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" detect-languages
```

**Inputs (Environment):**

- `REPOSITORY_CONFIG` - JSON config
- `SKIP_LANGUAGE_DETECTION` - Skip file scanning
- `BUILD_TARGET` - Comma-separated targets (all, go, python, etc.)
- `*_ENABLED` - Force enable/disable language builds

**Outputs:**

- `has-go` - Boolean
- `has-python` - Boolean
- `has-rust` - Boolean
- `has-frontend` - Boolean
- `has-docker` - Boolean
- `protobuf-needed` - Boolean
- `primary-language` - String (go, python, etc.)
- `go-matrix` - JSON matrix
- `python-matrix` - JSON matrix
- `rust-matrix` - JSON matrix
- `frontend-matrix` - JSON matrix
- `docker-matrix` - JSON matrix

**Dependencies:**

- `workflow_common.py`
- File system checks (Path().exists())

**Conversion Target:** `falkcorp/gha-detect-languages@v1`

---

#### Call #3: release_workflow.py release-strategy

**Location:** Job `detect-languages`, Step "Determine release strategy based on
branch"

```yaml
- name: Determine release strategy based on branch
  id: release-strategy
  env:
    BRANCH_NAME: ${{ github.ref_name }}
    INPUT_PRERELEASE: ${{ inputs.prerelease }}
    INPUT_DRAFT: ${{ inputs.draft }}
  run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" release-strategy
```

**Inputs (Environment):**

- `BRANCH_NAME` - Git branch (main, develop, feature/\*)
- `INPUT_PRERELEASE` - Force prerelease flag
- `INPUT_DRAFT` - Force draft flag

**Outputs:**

- `strategy` - stable, prerelease, or draft
- `auto-prerelease` - Boolean (was auto-detected)
- `auto-draft` - Boolean (was auto-detected)

**Logic:**

- `main` branch → `strategy=stable`, `auto-draft=true`
- `develop` branch → `strategy=prerelease`, `auto-prerelease=true`
- Feature branches → `strategy=prerelease`, `auto-prerelease=true`

**Dependencies:**

- `workflow_common.py`

**Conversion Target:** `falkcorp/gha-release-strategy@v1`

---

#### Call #4: release_workflow.py generate-version

**Location:** Job `detect-languages`, Step "Generate semantic release version"

```yaml
- name: Generate semantic release version
  id: version
  env:
    RELEASE_TYPE: ${{ inputs.release-type || 'auto' }}
    BRANCH_NAME: ${{ github.ref_name }}
    AUTO_PRERELEASE: ${{ steps.release-strategy.outputs.auto-prerelease }}
    AUTO_DRAFT: ${{ steps.release-strategy.outputs.auto-draft }}
  run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" generate-version
```

**Inputs (Environment):**

- `RELEASE_TYPE` - auto, major, minor, patch
- `BRANCH_NAME` - Git branch
- `AUTO_PRERELEASE` - From previous step
- `AUTO_DRAFT` - From previous step

**Outputs:**

- `tag` - Semantic version tag (v1.2.3)
- `version` - Version without prefix (1.2.3)
- `prerelease-suffix` - Suffix if prerelease (-alpha, -beta, etc.)

**Dependencies:**

- `workflow_common.py`
- `git` command (for tag inspection)

**Conversion Target:** `falkcorp/gha-generate-version@v1`

---

#### Call #5: release_workflow.py generate-changelog

**Location:** Job `finalize-release`, Step "Generate release changelog"

```yaml
- name: Generate release changelog
  id: changelog
  env:
    RELEASE_TAG: ${{ needs.detect-languages.outputs.release-tag }}
    PREVIOUS_TAG: ${{ steps.previous-tag.outputs.tag }}
  run: python3 "$GHCOMMON_SCRIPTS_DIR/release_workflow.py" "generate-changelog"
```

**Inputs (Environment):**

- `RELEASE_TAG` - Current release tag
- `PREVIOUS_TAG` - Previous release tag (for diff)

**Outputs:**

- `changelog_file` - Path to the release-notes Markdown file (commit list capped
  at 110,000 characters). Workflows read the notes from this file; never pass
  them through an action input, env var or argv (128 KiB per-string limit).
- `changelog_content` - The same notes inline. Kept only for an older
  `reusable-release.yml` paired with a newer script; new consumers use
  `changelog_file`.

**Dependencies:**

- `workflow_common.py`
- `git log` command

**Conversion Target:** `jdfalk/generate-changelog-action@v1`

---

#### Call #6: package_release_assets.py (Inline Python)

**Location:** Job `finalize-release`, Step "Package release artifacts"

```yaml
- name: Package release artifacts
  id: package
  shell: python
  run: |
    import os
    from pathlib import Path

    script_path = Path(os.environ.get("GHCOMMON_SCRIPTS_DIR", "")) / "package_release_assets.py"
    # ... inline script loading ...
```

**Note:** This is partially inlined, but imports from
`package_release_assets.py`.

**Inputs:**

- Artifacts from previous build jobs (uploaded via actions/upload-artifact)

**Outputs:**

- `assets` - JSON list of packaged assets
- `checksums` - SHA256 checksums file

**Conversion Target:** `falkcorp/gha-package-assets@v1`

---

## Workflow #3: reusable-protobuf.yml

**Purpose:** Generate Protocol Buffer code **Script Dependencies:** MEDIUM (2
scripts)

### Script Call Mapping

#### Call #1: parse_protobuf_config.py

**Location:** Job `generate`, Step "Parse buf.yaml configuration"

```yaml
- name: Parse protobuf configuration
  id: config
  run: python3 "$GHCOMMON_SCRIPTS_DIR/parse_protobuf_config.py"
```

**Inputs:**

- `buf.yaml` file in repository root

**Outputs:**

- `modules` - JSON array of buf modules
- `plugins` - JSON array of protoc plugins
- `languages` - Detected output languages

**Conversion Target:** `jdfalk/protobuf-config-action@v1`

---

#### Call #2: check_protobuf_artifacts.py

**Location:** Job `verify`, Step "Verify generated artifacts"

```yaml
- name: Check protobuf artifacts
  run: python3 "$GHCOMMON_SCRIPTS_DIR/check_protobuf_artifacts.py"
```

**Inputs:**

- Generated protobuf files from previous step

**Outputs:**

- Exit code (0 = success, 1 = missing files)
- Summary of generated files

**Conversion Target:** `jdfalk/protobuf-verify-action@v1`

---

## Workflow #4: reusable-maintenance.yml

**Purpose:** Dependency and security maintenance **Script Dependencies:** MEDIUM
(2 scripts)

### Script Call Mapping

#### Call #1: maintenance_workflow.py summarize-dependencies

```yaml
- name: Summarize dependencies
  env:
    DEPENDENCY_FILE: ${{ steps.snapshot.outputs.file }}
  run: |
    python3 "$GHCOMMON_SCRIPTS_DIR/maintenance_workflow.py" summarize-dependencies \
      --input "$DEPENDENCY_FILE" --output maintenance/dependency-summary.json
```

**Conversion Target:** `jdfalk/maintenance-summary-action@v1` (subcommand:
dependencies)

---

#### Call #2: maintenance_workflow.py summarize-security

```yaml
- name: Summarize security alerts
  run: |
    python3 "$GHCOMMON_SCRIPTS_DIR/maintenance_workflow.py" summarize-security \
      --input maintenance/security-alerts.json
```

**Conversion Target:** `jdfalk/maintenance-summary-action@v1` (subcommand:
security)

---

## Workflow #5: reusable-advanced-cache.yml

**Purpose:** Intelligent caching strategy **Script Dependencies:** HIGH (1
massive script)

### Script Call Mapping

#### Call #1: automation_workflow.py cache-plan

```yaml
- name: Generate cache plan
  id: cache-plan
  run: |
    python "$GHCOMMON_SCRIPTS_DIR/automation_workflow.py" cache-plan \
      --language "${LANGUAGE}" --workspace "${GITHUB_WORKSPACE}"
```

**Conversion Target:** `jdfalk/cache-strategy-action@v1`

---

#### Call #2: automation_workflow.py cache-key

```yaml
- name: Generate cache key
  id: cache-key
  run: |
    python "$GHCOMMON_SCRIPTS_DIR/automation_workflow.py" cache-key \
      --language "${LANGUAGE}"
```

**Conversion Target:** `jdfalk/cache-strategy-action@v1` (different mode)

---

## Workflow #6: documentation.yml

**Purpose:** Automated documentation generation **Script Dependencies:** HIGH (1
large script)

### Script Call Mapping

#### Call #1: docs_workflow.py (multiple subcommands)

```yaml
- run: python3 "$GHCOMMON_SCRIPTS_DIR/docs_workflow.py" generate-api-docs
- run: python3 "$GHCOMMON_SCRIPTS_DIR/docs_workflow.py" generate-readme
- run: python3 "$GHCOMMON_SCRIPTS_DIR/docs_workflow.py" generate-changelog
```

**Conversion Target:** `falkcorp/gha-docs-generator@v1` (multi-mode)

---

## Workflow #7: issue-automation.yml

**Purpose:** Intelligent PR/issue labeling **Script Dependencies:** MEDIUM (1
script)

### Script Call Mapping

#### Call #1: intelligent_labeling.py

```yaml
- name: Generate label suggestions
  run: python3 "$GHCOMMON_SCRIPTS_DIR/intelligent_labeling.py"
```

**Conversion Target:** `jdfalk/intelligent-labeling-action@v1`

---

## Workflow #8: sync-receiver.yml

**Purpose:** Receive cross-repo sync operations **Script Dependencies:** HIGH (1
large script)

### Script Call Mapping

#### Call #1: sync_receiver.py

```yaml
- name: Process sync request
  run: python3 "$GHCOMMON_SCRIPTS_DIR/sync_receiver.py"
```

**Conversion Target:** `jdfalk/sync-receiver-action@v1`

---

## Language-Specific Workflows (release-\*.yml)

### release-go.yml

**Script:** `build_go_release.py` **Status:** ✅ **ALREADY IN ACTION**
(`jdfalk/release-go-action`)

---

### release-python.yml

**Scripts:**

- `detect_python_package.py`
- `run_python_release_tests.py`
- `write_pypirc.py`

**Status:** ✅ **MOSTLY IN ACTION** (`jdfalk/release-python-action`)
**Remaining:** Some detection logic could be extracted

---

### release-rust.yml

**Scripts:**

- `collect_rust_crate_metadata.py`
- `configure_cargo_registry.py`

**Status:** ✅ **MOSTLY IN ACTION** (`jdfalk/release-rust-action`)

---

### release-frontend.yml

**Scripts:**

- `detect_frontend_package.py`
- `get_frontend_working_dir.py`

**Status:** ✅ **MOSTLY IN ACTION** (`jdfalk/release-frontend-action`)

---

### release-docker.yml

**Scripts:**

- `detect_docker_config.py`
- `determine_docker_platforms.py`
- `validate_docker_compose.py`

**Status:** ✅ **MOSTLY IN ACTION** (`jdfalk/release-docker-action`)
**Remaining:** Detection scripts could be extracted for reuse

---

## Summary Statistics

### Scripts by Usage Frequency

| Script                      | Used By # Workflows | Priority | Conversion Status |
| --------------------------- | ------------------- | -------- | ----------------- |
| `workflow_common.py`        | 15+ (dependency)    | P1 🔥    | Needs action      |
| `load_repository_config.py` | 8                   | P1 🔥    | Needs action      |
| `ci_workflow.py`            | 1 (massive)         | P2       | Needs action      |
| `release_workflow.py`       | 1 (massive)         | P3       | Needs action      |
| `automation_workflow.py`    | 1 (massive)         | P7       | Needs action      |
| `maintenance_workflow.py`   | 1 (medium)          | P7       | Needs action      |
| `docs_workflow.py`          | 1 (medium)          | P7       | Needs action      |
| `parse_protobuf_config.py`  | 1                   | P5       | Needs action      |
| `sync_receiver.py`          | 1 (large)           | P7       | Needs action      |
| `intelligent_labeling.py`   | 1                   | P7       | Needs action      |
| All others                  | 1 or embedded       | P4-P8    | Lower priority    |

---

## Conversion Priority Matrix

### Phase 1: Blocking Issues (Week 1)

1. **load-config-action** - Used by all workflows
2. **workflow-common-action** OR embed in all actions

### Phase 2: High-Impact (Week 2)

3. **ci-generate-matrices-action**
4. **ci-run-linters-action** (optional - could use super-linter directly)

### Phase 3: Release Pipeline (Week 3)

5. **detect-languages-action**
6. **release-strategy-action**
7. **generate-version-action**
8. **package-assets-action**

### Phase 4: Specialized (Week 4+)

9. **protobuf-config-action**
10. **protobuf-verify-action**
11. **cache-strategy-action**
12. **maintenance-summary-action**
13. **docs-generator-action**
14. **intelligent-labeling-action**
15. **sync-receiver-action**

---

## Next Phase: Architecture Design

With the usage map complete, we can now design:

1. **Action input/output contracts** - Formal specifications
2. **Dependency resolution strategy** - How to handle workflow_common.py
3. **Testing strategy** - How to validate actions work correctly
4. **Migration path** - How to update workflows without breaking existing users

---

**End of Usage Mapping Document**
