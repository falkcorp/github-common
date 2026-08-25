### Fixed

- **Stable releases built the newest RC instead of the requested version.**
  `goreleaser` derives its version from the tag `git describe` resolves at
  HEAD. On a repo that cuts an RC per merge that tag is always an RC, so a
  dispatch for `v0.219.1` built `v0.219.1-rc.96` and then failed with
  `422 already_exists` uploading assets the rc.96 release already had — leaving
  an empty draft behind and no stable published. `reusable-release.yml` now
  exports `GORELEASER_CURRENT_TAG` explicitly. `gha-release-go` creates the tag
  but never exported this variable, despite a pin comment claiming it did.
- `CURRENT_TAG` now uses the resolved release tag rather than
  `github.ref_name`, which is `main` on a `workflow_dispatch` and so made the
  previous-stable self-exclusion silently do nothing.
