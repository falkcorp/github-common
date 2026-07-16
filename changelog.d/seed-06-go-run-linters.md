### Added

#### `reusable-release.yml` — `go-run-linters` input forwards to `gha-release-go`'s `run-linters`

Consumer repos whose Go code requires a `GOEXPERIMENT` value (e.g. `jsonv2`)
could set `go-experiment` but had no way to skip the release workflow's
redundant `go vet` pass — `gha-release-go`'s lint step doesn't currently set
`GOEXPERIMENT` from its `go-experiment` input, so any repo relying on that
experiment fails `go vet` on every release even though CI already vetted the
same commit correctly. Added `go-run-linters` (default `true`, preserves
existing behavior) so callers can pass `go-run-linters: false` until the root
cause is fixed upstream in `gha-release-go`.
