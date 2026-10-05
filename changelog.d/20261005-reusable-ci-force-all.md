### Fixed

#### Scheduled and manually dispatched `reusable-ci.yml` runs now run the jobs

`detect-changes` diffed `github.event.before || github.sha` against
`github.sha`. A `schedule` or `workflow_dispatch` event has no `before`, so the
base fell back to the head commit and the run compared the commit with itself:
every category reported unchanged and every language job skipped. In
`falkcorp/audiobook-organizer` the nightly caller skipped `Go CI` on 5 of 5
scheduled runs checked, so the full non-short race suite never ran nightly.

New input `force-all` (string, default `'auto'`):

- `'auto'` forces on `schedule` and `workflow_dispatch`, diffs otherwise.
- `'true'` always forces; `'false'` always diffs.

A forced run reports a category as changed when the repository tracks at least
one file matching that category's filter (`git ls-files` with `:(glob)`
pathspecs), so forcing never starts `rust-ci` in a repo with no Rust. The
filter list is now defined once (`CHANGE_FILTERS`) and read by both paths. The
Change Detection summary prints which mode ran, and `detect-changes` exposes a
`force-all` output.

`workflow-lint` and `workflow-scripts` drop their separate
`|| github.event_name == 'workflow_dispatch'` bypass; the forced inventory now
covers that case. The only behavior change there is for a caller that sets
`force-all: 'false'` and dispatches manually — those two jobs then follow the
diff like everything else.

Callers affected by the `'auto'` default: this repo's own weekly `ci.yml`
schedule and any caller on `@main` that dispatches manually
(`cockroach-rollout-agent`). SHA-pinned callers change only when they bump.
