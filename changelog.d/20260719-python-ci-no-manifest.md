### Fixed

#### `reusable-ci.yml` — Python CI no longer fails in repos without a dependency manifest

The Python job set `cache: pip` unconditionally, and `actions/setup-python`
fails the job outright when it finds no `requirements.txt` or `pyproject.toml`:
`No file in ... matched to [**/requirements.txt or **/pyproject.toml]`.

Any repository that acquired its first Python file while having no dependency
manifest hit this — a single stdlib-only script is enough to activate the job.
It surfaced when `scripts/assemble_todo.py` was added to
`falkcorp/cockroach-rollout-agent`, a repo with no Python at all, turning a
previously green CI red.

The manifest is now detected first and the pip cache is requested only when
there is something to cache; otherwise setup runs uncached and emits a notice.
