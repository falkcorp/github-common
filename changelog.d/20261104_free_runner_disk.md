### Added

#### `reusable-ci.yml`: opt-in `free-runner-disk` input for Go CI

A new boolean input, `free-runner-disk` (default `false`). When it is true on
a Linux runner, the Go CI job removes the preinstalled .NET, Android, GHC and
CodeQL toolchains (about 25 GB) before `setup-go` restores its cache. A
caller with a large Go cache and `-race` test binaries was running the
hosted runner out of disk (`final link failed: No space left on device`).
Existing callers are unaffected.
