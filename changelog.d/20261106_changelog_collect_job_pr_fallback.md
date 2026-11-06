### Fixed

#### `reusable-release.yml`: changelog collection no longer blocks publishing, and lands through a PR when the default branch refuses pushes

Changelog collection was the last step of `create-release`, ahead of the step
that writes `release-created`. When its push to the default branch was refused
(a ruleset or merge queue with no bypass: `GH013`), the job failed before that
output existed, so `publish-github-packages` and `update-floating-tags` were
skipped for a release that had been created with all its assets.

- Collection is now its own job, `collect-changelog`, that runs after
  `create-release` once the release exists. Its failure turns the run red but
  cannot skip publishing.
- It still tries the direct push first, as before. On a protection or ruleset
  refusal it stops retrying and opens a pull request from
  `changelog/collect-<version>` with auto-merge (rebase) enabled, which a merge
  queue then takes. The PR is opened with the `CI_APP_ID` App token when
  configured, since a PR opened with `GITHUB_TOKEN` starts no `pull_request`
  checks and could never merge; it falls back to `JF_CI_GH_PAT`, then
  `GITHUB_TOKEN`, with a warning. The PR commit drops `[skip ci]` and its title
  carries `[skip changelog]`.
- It still collects only the fragments in the released commit.
