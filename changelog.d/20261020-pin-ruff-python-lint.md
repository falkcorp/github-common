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
  the pinned constant) passed to the step as `RUFF_VERSION`. It takes a bare
  version such as `0.17.0`; a leading `v` is stripped.
- The `CI Self Tests` lint step in `ci-tests.yml` also installed ruff unpinned;
  it now installs `ruff==0.17.0`.
- `ci_workflow.py` itself now passes the repo-root `ruff.toml` (31 missing
  docstrings, the `_CONFIG_CACHE` global replaced by `functools.lru_cache`, and
  the urllib fallback refusing non-https URLs), which the Python CI check
  requires.

#### Rollout: the pin reaches consumers in a follow-up PR

`reusable-ci.yml` checks out `ci_workflow.py` from the ref in the caller's
`.github/ghcommon-ref.txt`, or from the hard-coded fallback SHA (currently
`1f0d70e`) when the caller has no such file. Neither ref contains this change,
and this PR cannot name its own merge SHA. As with github-common#374 (the
fallback moved to `1f0d70e` afterwards, in `4b163cf`), the SHA bump is a
follow-up PR: after this merges, point the five fallback `ref=` lines in
`reusable-ci.yml` at the merge commit. Until then the `ruff-version` input is
accepted but has no effect, and the lint step is unchanged for everyone.

Known `reusable-ci.yml` consumers once the fallback moves:

- `cockroach-rollout-agent` (`@main`, has Python): moves to ruff 0.17.0
  automatically, unless it has its own `ghcommon-ref.txt`.
- `magnet-handler` and `migrate-loop`: pinned to older workflow SHAs, so
  unaffected until they bump.
- `audiobook-organizer`: needs both its `reusable-ci.yml` pin and its
  `.github/ghcommon-ref.txt` bumped to a commit that includes this change.

A repo that formats with a newer ruff than 0.17.0 can set
`with: ruff-version: "<bare version>"` on its `reusable-ci.yml` call instead of
waiting for `RUFF_VERSION` to move. The separate `Lint Python workflow scripts`
job in `reusable-ci.yml` still pins `ruff==0.16.10` on its own; a TODO comment
there marks it for unification.
