### Added

- `reusable-ci-minimal.yml`: new `run-go-tests` input (boolean, default `true`). Callers that run their own sharded Go test jobs pass `false` to skip the built-in `Go Tests (short, race)` job while keeping `Go Vet & Build`, `Go Lint`, the frontend jobs and the summary. Existing callers are unchanged; `Minimal CI Summary` already lists a skipped job as "skipped" and fails only on "failure".
