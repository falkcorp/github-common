### Added

#### `reusable-ci.yml` gains a `run-frontend` input to skip the frontend jobs

`reusable-ci.yml` had no way to skip its frontend half; only
`reusable-ci-minimal.yml` had `run-frontend`. A caller that installs its web
dependencies through its own script (for example because the frontend depends
on a sibling workspace package that a plain `npm ci` cannot resolve) still got
`frontend-npm-cache` and `frontend-ci` running their own install.

`run-frontend` (boolean, default `true`, same name and meaning as in the minimal
workflow) is applied in the change-detection gate: when `false`, the
`frontend-files` output is forced to `false`, so `frontend-npm-cache` and
`frontend-ci` are skipped through their existing `if:` conditions. `ci-summary`
already maps a skipped frontend job to `skipped`, which is not a failure. The
default keeps every existing caller's behaviour unchanged.
