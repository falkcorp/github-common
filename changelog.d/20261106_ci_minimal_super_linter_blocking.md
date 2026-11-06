### Added

#### `reusable-ci-minimal.yml`: `super-linter-blocking` input lets a caller make Super Linter a gate

Super Linter has always run in advisory mode here (`DISABLE_ERRORS=true` plus `continue-on-error`). Nothing could make it
block, so a repo that wanted its Markdown or YAML lint to stop a merge had to keep running its own linter action outside
the shared workflow. infra-docs is the first such repo. The new `super-linter-blocking` input defaults to `false`. When it
is `true`, both of those switches flip, the job drops "(advisory)" from its name, and a super-linter failure fails
`Minimal CI Summary`. The caller's `super-linter-*.env` still cannot turn blocking on or off by itself.

#### `reusable-ci-minimal.yml`: `run-go-vet-build` input for repos without a Go module

`Go Vet & Build` was the only job with no `if:`. In a repo with no `go.mod` (a docs-only repo, for example) it ran
`go vet ./...`, which failed, so those repos could not call this workflow at all. `run-go-vet-build` defaults to `true`,
so existing callers are unchanged.
