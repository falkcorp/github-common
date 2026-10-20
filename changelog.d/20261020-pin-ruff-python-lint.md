### Fixed

#### The shared Python lint now runs a pinned ruff

`ci_workflow.py python-lint` ran `pip install --upgrade ruff` whenever ruff was
not on `PATH`, so every consumer linted with whatever ruff was newest and a new
release could break all of their CI overnight. It also ran whichever `ruff` the
`PATH` resolved, so an already-installed ruff of another version (pipx, the
runner image) was used silently.

- `RUFF_VERSION = "0.17.0"` in `ci_workflow.py` is the single pinned version
  (the one `audiobook-organizer` formats against). The step installs
  `ruff==<version>` with `sys.executable -m pip` whenever the interpreter's ruff
  differs, re-checks the version, and raises on a mismatch.
- ruff is invoked as `python -m ruff`, so the verified install is the one that
  runs.
- `reusable-ci.yml` gains an optional `ruff-version` input (default empty, meaning
  the pinned constant) passed to the step as `RUFF_VERSION`.
- The `CI Self Tests` lint step in `ci-tests.yml` also installed ruff unpinned;
  it now installs `ruff==0.17.0`.
