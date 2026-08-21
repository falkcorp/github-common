# Repo Flavors

Three flavors are supported. The flavor selects which overlay files `bootstrap_repo.sh`
seeds and which template repo `gh repo create --template` uses (when present).

The fuller per-flavor file inventory lives in `docs/standards/{flavor}-repo.md` once
ghcommon issue #265 lands. Until then, this file is the working spec.

## action

GitHub Actions repo (composite, JS, or Docker action).

**Overlay files seeded if missing**

- `action.yml` — composite stub
- `TODO.md` — empty `# TODO` header

**Template repo**: `jdfalk/jft-github-actions` (exists; verified template flag set)

**Notable required files** (from `ACTION_REPO_STANDARDS.md`):

- `action.yml`, `README.md`, `CHANGELOG.md`, `TODO.md`, `ruff.toml`
- `.pre-commit-config.yaml`, `.yamllint`
- `.github/dependabot.yml`, `.github/copilot-instructions.md`
- For Docker actions: `Dockerfile`, `.github/workflows/publish-docker.yml`

## library

Reusable library (Go module, Rust crate, Python package, npm package, etc).

**Overlay files seeded if missing**

- `CHANGELOG.md` — Keep-a-Changelog template

**Template repo**: `jdfalk/jft-library-template` (does not yet exist; falls back to empty)

**Notable required files**

- `README.md` with usage section, `CHANGELOG.md`, `LICENSE`
- Language-appropriate manifest (`go.mod`, `Cargo.toml`, `pyproject.toml`, `package.json`)
- `.github/dependabot.yml`, `.github/copilot-instructions.md`, `.github/instructions/`

**Public API surface**: any breaking change requires a CHANGELOG entry under
`## [Unreleased]` before the merge.

## service

Deployable application or service.

**Overlay files seeded if missing**

- `Dockerfile` — `FROM scratch` placeholder

**Template repo**: `jdfalk/jft-service-template` (does not yet exist; falls back to empty)

**Notable required files**

- `README.md` with **Deployment** section, `LICENSE`
- `Dockerfile`
- `.github/workflows/publish-docker.yml` (recommended)
- `.github/dependabot.yml`, `.github/copilot-instructions.md`, `.github/instructions/`

## cli

Distributable binary or CLI tool, shipped via goreleaser / brew / winget /
direct install scripts — **not** a containerized service.

**Overlay files seeded if missing**

- `CHANGELOG.md` — Keep-a-Changelog template (same as library)

**Template repo**: `jdfalk/jft-cli-template` (does not yet exist; falls back to empty)

**Notable required files**

- `README.md` with **Installation** section (per-platform install steps), `LICENSE`
- `CHANGELOG.md`
- `.goreleaser.yml` or equivalent release config (tool-specific; not seeded by skill)
- Language-appropriate manifest (`go.mod`, `Cargo.toml`, etc)
- `.github/dependabot.yml`, `.github/copilot-instructions.md`, `.github/instructions/`

**Differs from `service`**: no `Dockerfile`. CLIs are distributed as native binaries
to user machines, not deployed as containers. Differs from `library`: produces a
binary artifact, not an importable package; CHANGELOG drives the release tag, not
a SemVer of an exported API.

## Common to all flavors

These come from `ghcommon/scripts/sync-repo-setup.py`, regardless of flavor:

- `.github/instructions/*.instructions.md` — language-specific coding standards
- `.github/copilot-instructions.md` — AI agent context
- `.github/AGENTS.md` and related AI files
- `.github/dependabot.yml` — language-aware dependabot config
- `.github/repository-config.yml` — seeded with `repository.type: <flavor>`

Repo settings are flavor-independent. Branch rules come from org-wide rulesets,
not per-repo protection — see `references/branch-protection.md`.

## Adding a new flavor

1. Decide on overlay files in `bootstrap_repo.sh`'s `case "${FLAVOR}"` block.
2. Add it to `--flavor` validation in `bootstrap_repo.sh`.
3. Document its file list in `docs/standards/<flavor>-repo.md`.
4. (Optional) create `jdfalk/jft-<flavor>-template` and flip `isTemplate: true`.
5. Add to this doc.
