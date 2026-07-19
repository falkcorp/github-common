### Added

#### `TODO.md` is now assembled from `todo.d/` fragments

New tasks are added by dropping a uniquely-named Markdown fragment in `todo.d/`
instead of editing `TODO.md` directly, so parallel PRs never collide on the TODO
list — the same problem, and the same fragment-per-change solution, that
`changelog.d/` + `scriv` already solve for `CHANGELOG.md`.

`scriv` is changelog-only and has no TODO equivalent, so assembly is done by a
new `scripts/assemble_todo.py`. It folds every fragment in below the
`<!-- todo-insert-here -->` marker in the new `## 📥 Inbox` section, bumps
`TODO.md`'s version header, and `git rm`s the fragments it consumed so the
insertion and removals land in one commit. `.github/workflows/todo-collect.yml`
runs it daily and on `workflow_dispatch`.

The system is **add-only** — fragments add tasks; checking one off or promoting
it out of the Inbox stays a direct edit of `TODO.md`. It is **opt-in by presence
of `todo.d/todo.ini`**, so the workflow is a no-op in any repo that has not
adopted it. Unlike the changelog system there is deliberately **no PR check**:
adding a task is optional, not something to enforce on every code PR.
