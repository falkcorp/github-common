### Fixed

#### `reusable-release.yml` — bump `gha-release-go` pin to fix same-commit tag ambiguity

Bumped to `gha-release-go@e6b2fa7` (v2.0.1), which pins `GORELEASER_CURRENT_TAG`
explicitly instead of letting GoReleaser infer it via `git describe`. Without
this, a concurrent release process (e.g. a `Prerelease on Merge` run triggered
by a routine PR merge) tagging the same commit could cause `describe` to resolve
to the wrong tag, making GoReleaser build under that tag and collide with the
other release's already-uploaded assets (`422 already_exists`). Reproduced 3
times in a row on `falkcorp/audiobook-organizer`.
