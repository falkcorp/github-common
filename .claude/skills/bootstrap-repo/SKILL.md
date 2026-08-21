---
name: bootstrap-repo
description: Create a new GitHub repo or apply ghcommon house standards to an existing one. Use when the user says "create a new repo", "bootstrap a repo", "set up a new repo to our standards", "apply our standards to repo X", "make this repo compliant", "new action/library/service/cli repo", or wants merge settings, branch protection, labels, dependabot, and instruction files configured in one shot. Wraps gh repo create, applies repo-level settings (rebase-only, auto-merge, no delete), runs ghcommon's label and instruction-file sync scripts, seeds flavor-specific overlay files, and records the bootstrap in ghcommon/.github/bootstrapped-repos.json.
---

# bootstrap-repo

Apply the full jdfalk/ghcommon house standard to a repo: settings, labels,
dependabot, instruction files, flavor overlay. Branch rules come from the
org-wide rulesets, NOT per-repo protection.

## When to use

- Creating a brand-new repo (`--mode create`)
- Bringing an existing repo into compliance (`--mode adopt`)
- Re-running for idempotency / drift correction

## How it works

The skill is a thin wrapper. The actual work is in `scripts/bootstrap_repo.sh`,
which orchestrates:

1. `gh repo create` (create mode) or `gh repo view` (adopt mode)
2. `apply_repo_settings.sh` — `PATCH /repos/:o/:r` with merge/visibility settings
3. `ghcommon/scripts/sync-repo-setup.py` — copies instructions, dependabot, etc
4. `ghcommon/scripts/sync-github-labels.py` — applies all labels from `labels.json`
5. Flavor-specific overlay (action.yml, CHANGELOG.md, Dockerfile)
6. Seed `.github/repository-config.yml` with `repository.type: <flavor>`
7. Initial bootstrap commit + push to `main`
8. `verify_bootstrap.sh` — read-back diff against expected state

Branch protection is intentionally NOT applied — see
`references/branch-protection.md`. falkcorp uses org-wide rulesets; classic
per-repo protection has no bypass list and deadlocked 15 repos.

## Decision tree

**Pick the mode.**

- New repo doesn't exist yet → `--mode create`
- Repo already exists → `--mode adopt`

**Pick the flavor.** See `references/flavors.md` for full file lists.

- Building a GitHub Action → `--flavor action`
- Building a reusable library/SDK/package → `--flavor library`
- Building a deployable service or app (containerized) → `--flavor service`
- Building a distributable binary/CLI (goreleaser, brew, etc) → `--flavor cli`

## Usage

```bash
# Create a new private library repo
.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh \
    --flavor library --mode create --name my-new-thing

# Adopt an existing service repo
.claude/skills/bootstrap-repo/scripts/bootstrap_repo.sh \
    --flavor service --mode adopt --name existing-service

# Common flags
#   --owner OWNER         (default: jdfalk)
#   --private | --public  (default: --private; create mode only)
#   --ghcommon PATH       (default: ~/repos/github.com/jdfalk/ghcommon)
#   --repo-path PATH      (skip clone, use this checkout)
#   --skip-labels         (don't sync labels)
```

## Verification

After running, `verify_bootstrap.sh` runs automatically and exits non-zero on drift.
Standalone use:

```bash
.claude/skills/bootstrap-repo/scripts/verify_bootstrap.sh \
    --owner jdfalk --repo my-thing --flavor library
```

## Registry

Every successful bootstrap appends/updates `ghcommon/.github/bootstrapped-repos.json`.
Schema: `{version, repos: [{owner, name, flavor, mode, first_bootstrapped, last_bootstrapped}]}`.
Idempotent (existing entries get `last_bootstrapped` refreshed; `first_bootstrapped`
is preserved).

The skill writes the file but does not commit it. Commit it from ghcommon to share
across machines and to enable future "bootstrap-all" sweeps.

## What this skill does NOT do

- **Secrets** — does not seed `CI_APP_ID` or any other secret. Run
  `ghcommon/scripts/setup-ci-app.sh` after bootstrap. Tracked: ghcommon issue #264.
- **Default branch rename** — assumes `main`; manual fix needed for `master` repos.
- **Create org/personal templates** — uses `jdfalk/jft-<flavor>-template` if it
  exists; falls back to empty. The library and service templates don't exist yet.
- **Modify existing files** — `sync-repo-setup.py` is version-aware and won't
  clobber locally-modified files.

## References

- `references/repo-settings.md` — every repo-level setting and why
- `references/branch-protection.md` — why classic protection is NOT applied
- `references/flavors.md` — per-flavor file inventory
