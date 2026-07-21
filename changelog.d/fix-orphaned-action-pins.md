### Fixed

#### Repoint 6 orphaned `falkcorp/gha-release-*` action pins that crashed Dependabot

`reusable-release.yml` pinned six first-party actions (gha-release-python/docker/go/rust/frontend,
gha-package-assets) to commit SHAs labelled with `v2.0.x`/`v1.2.0` tags that were never published.
Those SHAs are unreachable from any tag, so Dependabot's `github_actions` updater crashed with
`no such commit …` — and because the ecosystem is part of the `multi-ecosystem-group`, the crash
blocked all grouped version-update PRs (none created since 2026-06-04). Repinned each to its latest
real release (v1.0.3 / v1.1.5).
