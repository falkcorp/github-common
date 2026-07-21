### Fixed

#### Rust CI no longer fails with "Unknown command: rust-build"

The Rust job invoked `gha-ci-workflow-helpers` with `command: rust-build` and
`command: rust-test`, but that action never implemented either command — only
`rust-format` and `rust-clippy` exist, in every release through v1.1.7. So every
repository whose Rust CI actually ran failed at the build step with
`Unknown command: rust-build`.

The build and test steps now run `cargo build --release` / `cargo test --release`
inline. Format and clippy still go through the action, which does support them.
Surfaced by falkcorp/cockroach-rollout-agent, whose Rust CI activated for the
first time during the TODO fan-out.
