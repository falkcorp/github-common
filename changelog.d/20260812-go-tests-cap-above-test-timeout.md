### Fixed

#### `Go Tests (short, race)` can now reach its own `go test` timeout

The job capped at 20 minutes while its test step ran `go test -short -race
-timeout 30m ./...`. The runner therefore killed the job ten minutes before
Go's own timeout could fire — and Go's `-timeout` is the only thing that prints
a goroutine dump naming the stuck test. Every slow run produced
`conclusion=cancelled` with no diagnostic output at all, and `cancelled`
renders on a PR as a test failure even though nothing failed.

Observed repeatedly in `falkcorp/audiobook-organizer` (#2311, #2315, #2319 —
the last cancelled at exactly 20m16s on a docs-only PR, with every other job in
the run green). Consuming repos could not work around it: this workflow exposes
no timeout input, so the cap is only settable here.

The cap is now 35, and the invariant is stated in a comment beside it: **the
job cap must stay strictly greater than the longest `-timeout` passed to any
`go test` invocation in the job, plus setup.** Raising the test timeout without
raising the cap silently makes every slow run undiagnosable again.

Raising a job cap cannot turn a passing run into a failing one — it only lets a
genuinely slow or hung run survive long enough to emit the dump that identifies
the culprit. Suites finishing well under 20 minutes are unaffected.
