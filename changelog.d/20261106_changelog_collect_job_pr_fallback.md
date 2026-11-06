### Fixed

#### `reusable-release.yml`: changelog collection no longer blocks publishing, and lands through a PR when the default branch refuses pushes

Changelog collection was the last step of `create-release`, ahead of the step
that writes `release-created`. When its push to the default branch was refused
(a ruleset or merge queue with no bypass: `GH013`), the job failed before that
output existed, so `publish-github-packages` was skipped for a release that had
been created with all its assets.

- Collection is now its own job, `collect-changelog`, after `create-release`.
  Its failure turns the run red but cannot skip publishing. `build-status` waits
  for it.
- A first step decides whether there is anything to collect (the released
  commit is on the default branch, which a tag-push release also passes, `changelog.d/scriv.ini` and the CHANGELOG marker exist,
  fragments are pending) before any token is minted.
- It collects at the released commit and checks the commit touches only
  `CHANGELOG.md` and `changelog.d/`, then cherry-picks that one commit onto a
  fresh fetch of the default branch. The old step pushed (or rebased) the
  checkout's own history, so a release cut from another branch could carry
  that branch's commits to the default branch.
- It still tries the direct push first. On a protection or ruleset refusal it
  opens a pull request from `changelog/collect-<version>` with the `CI_APP_ID`
  App token, or `JF_CI_GH_PAT` if the App cannot, and enables rebase auto-merge
  (falling back to a plain rebase merge, which enqueues on a merge-queue
  branch). A PR opened with `GITHUB_TOKEN` starts no checks, so that token is
  not used for it. The PR commit drops `[skip ci]`; its title carries
  `[skip changelog]`.
- It refuses to collect while an earlier version's `changelog/collect-*` PR is
  still open, so fragments are never filed under two versions. A re-run of the
  same version reuses its own PR, and a token that cannot list pull requests
  only warns, so repos that push directly are unaffected.
