### Fixed

#### `reusable-ci.yml` — Changelog Fragment Check no longer fails dependabot PRs

The `changelog-fragment-check` job required a `changelog.d/` fragment on every
pull request, including dependabot dependency-bump PRs — which have no way to
run `scriv create` and aren't the kind of user-facing change a fragment is for.
The job now skips (with a `::notice::`) whenever the PR author is
`dependabot[bot]`, checked before the existing `skip-changelog` label / `[skip
changelog]` title escape hatches.

### Added

#### `CLAUDE.md` — worktree discipline mandate

Documented the same worktree-first discipline already enforced in other
`falkcorp` repos: never edit or commit directly on `main`, always create a
`.worktrees/<branch>` worktree first, and remove it after the PR merges. This
repo publishes the reusable workflows every `falkcorp` repo's CI depends on, so
a bad direct-to-`main` edit has org-wide blast radius.
