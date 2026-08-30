### Changed

#### Go standards: 1.27 preferred where dependencies allow, `io/ioutil` banned

1.26 is restated as both the minimum and the default — `go.mod` and every CI
`go-version` pin — and 1.27 becomes the preferred target for any repo whose full
dependency graph builds, vets and tests clean on it. A repo that could be on
1.27 and sits on 1.26 with no stated reason is drift rather than a decision, and
the check is a build (`GOTOOLCHAIN=go1.27.0 go build ./... && go vet ./...`)
rather than a guess.

The worked example is a repo that genuinely cannot move.
`audiobook-organizer` fails to declare `go 1.27.0` because
`github.com/cockroachdb/swiss`, reached transitively through
`github.com/cockroachdb/pebble/v2/internal/cache`, gates its runtime-introspection
file on `//go:build (go1.20 && !go1.27) || untested_go_version` and says in the
file that it requires manual verification with each Go release. The standard now
states the rule that follows: never force such a bump with
`-tags untested_go_version`, a fork, or a `replace` directive, because that
converts a loud compile error into the silent runtime corruption the gate exists
to prevent. Wait for upstream and record the blocker by name.

Also adds a deprecated-standard-library table banning `io/ioutil`. The import
itself is the smell, so the check is a grep for the package rather than for
individual functions, and the table flags the one entry that is not a pure
rename: `os.ReadDir` returns `[]os.DirEntry`, skipping a `stat` per entry, so
`.Info()` should be called only where it is actually needed.
