<!-- file: .github/copilot-instructions.md -->
<!-- version: 2.5.0 -->
<!-- guid: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a -->
<!-- last-edited: 2026-07-21 -->

# github-common — Additional Context

Org-wide coding standards (file headers, language rules, commit format) are at
**<https://github.com/falkcorp/.github>** and apply automatically to this repo.

For full project context: **CLAUDE.md** at the repo root.

## Project overview

Reusable GitHub Actions workflows, scripts, and multi-repo automation. Language: Python.

## Key directories

| Path | Purpose |
|---|---|
| `.github/workflows/reusable-*.yml` | Reusable workflows called by other repos |
| `scripts/` | Python automation tools for cross-repo operations |
| `.github/instructions/` | Modular AI agent rules with language targeting |

## Critical constraints

- `scripts/intelligent_sync_to_repos.py` — propagates changes to target repos; use `--dry-run` first
- `scripts/workflow-debugger.py` — analyzes workflow failures; outputs to `workflow-debug-output/fix-tasks/`
- All commits must use conventional commit format: `type(scope): description`

## 📝 Changelog & TODO — Use the Fragment System (MANDATORY)

**Do not hand-edit `CHANGELOG.md`, and do not add new tasks straight into the
`TODO.md` inbox.** Both files are assembled from per-change fragments so that
parallel PRs never collide on them.

- **`CHANGELOG.md` is assembled, not hand-edited.** Add a fragment under
  `changelog.d/` (run `scriv create`, or write the Markdown file by hand). The
  fragments are folded into `CHANGELOG.md` at release time by `scriv`, and a CI
  check (`changelog-check.yml`) requires one on each PR. See `changelog.d/README.md`.
- **New `TODO.md` tasks are added via fragments.** Drop a Markdown fragment in
  `todo.d/` (see `todo.d/README.md`) instead of editing the `## 📥 Inbox`
  section. `scripts/assemble_todo.py` folds fragments in daily. This is
  **add-only**: checking a task off or removing it is a normal direct edit of
  `TODO.md`.
