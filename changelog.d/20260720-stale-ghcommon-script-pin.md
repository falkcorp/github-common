### Fixed

#### Reusable workflows no longer fetch four-month-stale helper scripts

Every reusable workflow that checks out this repo's own
`.github/workflows/scripts` fell back to a hardcoded
`e04c222a0366d5801d3b02bb76519f19ba1fa440` when the calling repo had no
`.github/ghcommon-ref.txt`. That commit is from **2026-03-28**.

Callers consume the workflows at `@main`, so current workflow logic was invoking
helper subcommands that the pinned script predates. Rust CI failed outright with
`##[error]Unknown command: rust-build` in every repo without the ref file — the
`rust-*` commands were added in 767acd4 on **2026-05-27**, two months after the
pin.

All 11 occurrences across 6 workflows now point at current `main`, and the
fallback carries a comment explaining that it must be kept in step with the
workflows it ships alongside.
