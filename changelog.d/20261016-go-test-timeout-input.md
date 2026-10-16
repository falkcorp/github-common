### Added

#### `reusable-ci.yml` takes a `go-test-timeout` input

The Go CI job's test step runs the `go-test` command of
`gha-ci-workflow-helpers`, whose embedded Python calls
`go test -v -race -coverprofile=... ./...` with no `-timeout`. Go's default of
10 minutes per test binary therefore applied, and a caller had no way to raise
it: a calling workflow cannot pass env into a reusable workflow's jobs, and the
action has no timeout input. `falkcorp/audiobook-organizer`'s `internal/database`
package runs 510–600s under `-race` there and was failing at the 10m mark.

The new input is a Go duration (e.g. `25m`). When set, the Go test steps run
with `GOFLAGS=-timeout=<value>`; `go test` takes test flags from `GOFLAGS`, and
`go build` / `go tool cover` ignore flags they do not know, so only the tests
see it. Empty (the default) leaves behavior unchanged.

The Go CI job cap moves from 40 to 60 minutes so it stays above setup + the
slowest suite + the test timeout for values up to 30m; the comment beside it
states that invariant.
