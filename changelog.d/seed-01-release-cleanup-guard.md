### Fixed

#### `reusable-release.yml` — cleanup step no longer deletes the stable release it just created

The "Clean up superseded drafts and prereleases" step queries
`gh release list --json tagName,isDraft,isPrerelease` and deletes anything
matching drafts/prereleases with a version `<=` the new stable version, under
the assumption that the just-cut stable release (draft=false, prerelease=false)
is naturally excluded from that set. Observed on `falkcorp/audiobook-organizer`
v0.217.6: the just-created stable release's own tag showed up in that "drafts or
prereleases" set anyway (most likely a stale list read, or a leftover rolling
"next stable" draft placeholder reused under the same tag by the
release-creation step) and was deleted seconds after
`softprops/action-gh-release` logged "🎉 Release ready" — leaving the release
API 404ing on the tag it had just published. Added an explicit guard that skips
any tag exactly matching `$STABLE_VERSION`, independent of what
`isDraft`/`isPrerelease` report for it.
