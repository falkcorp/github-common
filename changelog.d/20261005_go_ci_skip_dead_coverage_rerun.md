### Fixed

#### reusable-ci: no dead coverage rerun, 40-minute Go CI cap

- "Generate Go coverage profile" and "Check Go test coverage" now run only when the repo has `.testcoverage.yml`. Without it the first step re-ran the whole suite (6–8 min) for a checker that exits immediately, which pushed audiobook-organizer's go-ci over its 30-minute cap.
- `go-ci` `timeout-minutes` is now 40, so a hung test is killed by Go's 10-minute test timeout (with a goroutine dump naming it) before the runner cancels the job.
