### Added

#### `reusable-ci-minimal.yml` can now run golangci-lint and Super Linter

`reusable-ci-minimal.yml` ran go vet, build, short tests and the frontend jobs,
but had no Go lint step at all — so a consuming repo shipping a `.golangci.yml`
never had it execute in CI. In `audiobook-organizer`, `golangci-lint` appeared in
zero workflows and `make ci` runs staticcheck instead, so its config had never run
in CI once since being added.

Two new opt-in jobs, both defaulting to `false`, so every existing caller's CI is
byte-identical until it opts in:

- **`go-lint`** installs `golangci-lint` at a pinned version via `go install` and
  runs it. The `golangci-lint-args` input exists so a repo can scope which linters
  actually gate CI (`--enable-only ...`). That matters more than it sounds: a repo
  config can legitimately enable a linter carrying a known backlog that CI must not
  fail on. In `audiobook-organizer` a bare `golangci-lint run ./...` exits non-zero
  on 927 pre-existing errcheck findings before any newly added linter is consulted,
  so without the selector, adding a gate to an existing config means inheriting its
  entire backlog on day one.
- **`super-linter`** runs in advisory mode. `DISABLE_ERRORS=true` is Super Linter's
  own switch (reports everything, exits 0); `continue-on-error` is the belt, so a
  repo shipping `DISABLE_ERRORS=false` in its own env file cannot start hard-failing
  its PRs the moment it opts in, and a future upstream rename of the flag cannot
  start blocking people either.

`go-lint` is wired into `ci-minimal-summary`'s **failure set**, not just its
`needs` — without that, an opted-in lint failure would be invisible to any caller
whose required check is the summary job, and the gate would be inert.
`super-linter` reports into the summary table only.
