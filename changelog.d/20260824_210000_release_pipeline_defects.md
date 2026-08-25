### Fixed

- **Release drafts are no longer duplicated on the same tag.** The draft lookup
  in `reusable-release.yml` used `gh release list` with no `--limit`, which
  defaults to 30. On repos carrying hundreds of RC prereleases the existing
  draft fell outside that window, the lookup returned empty, and each run
  created another draft on the same tag. Enumeration now uses
  `gh api --paginate`, and drafts are addressed by release `id` rather than by
  tag — several drafts can share a `tag_name`, since a draft has no git tag
  until published, so `gh release edit "$TAG"` was ambiguous. Duplicates left
  by earlier runs are collapsed automatically.
- **Release notes diff from the previous stable tag.** goreleaser's
  `{{ .PreviousTag }}` walks back exactly one tag, which on a
  prerelease-per-merge repo is nearly always an RC, so notes were generated
  against e.g. `v0.218.1-rc.181` and listed two commits.
  `GORELEASER_PREVIOUS_TAG` is now pinned to the newest stable tag, and left
  unset when no stable tag exists.

### Added

- **`disabled-languages` input for `reusable-release.yml`.** The six
  `*-enabled` booleans could only force a language *on*: they default to
  `false`, so an explicit `docker-enabled: false` was byte-identical to
  omitting it and both resolved to `auto` (detect and build anyway). There was
  no way to say "never build this". Pass e.g. `disabled-languages: 'python'`.
  Disabling takes precedence over a force-on.

### Changed

- **RC purging is now owned by the caller repo.** The "Clean up superseded
  drafts and prereleases" step is gated off; it competed with caller-side
  cleanup workflows on a different keep-count, making RC counts impossible to
  attribute. Gated rather than deleted because its draft-cleanup half has no
  replacement yet.
