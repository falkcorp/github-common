### Fixed

#### `ci-tests.yml`, `performance-monitoring.yml`: Rust Benchmarks pass the toolchain

`dtolnay/rust-toolchain` is pinned to a SHA on the action's `master` branch,
which has no default toolchain. The two Rust Benchmarks jobs called it without
`toolchain`, so the step failed with `'toolchain' is a required input` and
CI Self Tests and Performance Monitoring were red on every run since
February 2026. Both now pass `toolchain: stable`. The pin comment in all four
workflows that use the action said `# stable`; it now says `# master`, which
is what the SHA is.
