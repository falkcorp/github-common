### Added

#### `reusable-ci.yml` gains an opt-in `fetch-base-branch-tip` input for Go CI

The `go-ci` job checks the repository out at depth 1 with no base ref, so a Go
test that diffs a file against the default branch (for example a test that only
lets a list shrink) cannot resolve `origin/<default branch>` and fails. A caller
cannot add a step to a reusable workflow's job, so the fetch has to live here.

`fetch-base-branch-tip` (boolean, default `false`) adds a step right after
"Checkout repository" in `go-ci` that runs
`git fetch --no-tags --depth=1 origin "${DEFAULT_BRANCH}"` and then verifies
`origin/<default branch>` resolves. `DEFAULT_BRANCH` comes from
`github.event.repository.default_branch` through `env:`, not through script
interpolation. Only the default branch's tip is fetched, never its history. The
default keeps every existing caller's behaviour unchanged.
