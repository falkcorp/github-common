### Changed

#### `intelligent_sync_to_repos.py` now syncs the `todo.d/` scaffolding

The TODO fragment system's shared files — `todo.d/todo.ini`, its template and
README, `scripts/assemble_todo.py`, and `.github/workflows/todo-collect.yml` —
are added to `MANAGED_FILES`, so future syncs keep adopting repositories current
the same way they already do for `changelog.d/`.

`TODO.md` itself is deliberately **not** synced: it is repo-specific and carries
each repository's own `<!-- todo-insert-here -->` marker and curated sections.
