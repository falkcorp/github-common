### Fixed

#### `Workflow Scripts` passes: `.github/scripts` is ruff-clean and ruff is pinned

The job runs `ruff check` and `ruff format --check` over `.github/scripts` and
had 411 findings, so it failed on every run that reached it. That was every
manual dispatch, and since `force-all` (#369) also the weekly schedule.

- `ruff.toml` gives `.github/scripts/**` the same per-file ignores as
  `scripts/**` (`T20`, `S602`/`S603`/`S607`) plus `RUF001` (status emoji) and
  `PLR2004` (argv and semver-part counts).
- The remaining findings are fixed in code: docstrings, loop-variable
  shadowing, `raise ... from`, a scheme check before `urlopen`, a logged
  warning in place of `except: pass`, hoisted imports, `os.popen('date')`
  replaced by `datetime`, and unused parameters removed. `get_env_bool` in
  `determine-security-languages.py` now honors its `default` argument, which it
  used to ignore.
- The job installs `ruff==0.16.10` rather than the latest release, so a new
  ruff release can no longer fail it overnight.
