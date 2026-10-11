### Fixed

#### Reusable CI no longer runs language jobs for files that are not a project

`detect-changes` now checks the project entry point on diff runs, not only
on forced runs. Before this, a PR that touched a matching file always
started the language job:

- any `.js`, `.css` or `.html` file started `frontend-ci`, even with no
  `package.json`;
- any `.rs` file started `rust-ci`, even with no root `Cargo.toml`;
- any `.py` file started `python-ci`, even with no Python package.

Each job then failed. For example, a Rust binary that embeds a static
`app.js` failed `frontend-ci` on every PR that edited that file.

The checks themselves are unchanged. They moved from the forced-run
inventory into a "Gate categories on their project entry points" step that
runs in both modes. That step reads the frontend directory from the same
`gha-get-frontend-config` lookup that `frontend-ci` uses.
