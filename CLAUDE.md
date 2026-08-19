<!-- file: CLAUDE.md -->
<!-- version: 3.4.0 -->
<!-- guid: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f -->
<!-- last-edited: 2026-08-19 -->

# CLAUDE.md

> **NOTE:** This file is a pointer. All Claude/AI agent and workflow
> instructions are centralized in the `.github/instructions/` and
> `.github/prompts/` directories.

## Coding Standards

Org-wide coding standards are in the `.standards/` git submodule (cloned from
`https://github.com/falkcorp/.github`). Always clone with
`git clone --recurse-submodules` so these are available.

Key files:

- **File headers (MANDATORY):** `.standards/instructions/file-headers.md`
- **Commit format:** `.standards/instructions/commit-messages.md`

## Quick Reference

**Main Documentation:**

- [Copilot Instructions](.github/instructions/copilot-instructions.md) - Primary
  AI agent configuration
- [Instructions Directory](.github/instructions/) - All coding standards and
  language-specific rules
- [Prompts Directory](.github/prompts/) - Specialized prompts for specific tasks

**For complete list of all instruction files, see [AGENTS.md](AGENTS.md)**

## 🚨 CRITICAL: Documentation Update Protocol

This repository uses direct-edit documentation workflow:

- Edit documentation directly in target files
- Always update version headers when making changes
- Do not use legacy doc-update scripts (create-doc-update.sh,
  doc_update_manager.py)
- Follow semantic versioning for version numbers

**Exception — `CHANGELOG.md` is assembled, not hand-edited.** Do not edit
`CHANGELOG.md` directly. Add a changelog fragment under `changelog.d/` (run
`scriv create`, or write the Markdown file by hand) so parallel PRs never
collide on the changelog. The fragments are folded into `CHANGELOG.md` at
release time by `scriv`. See `changelog.d/README.md` and
`.github/prompts/ai-changelog.prompt.md`. This is a focused, tool-backed revival
of the fragment idea — not the retired bespoke JSON `doc_update_manager.py`
system.

**Exception — new `TODO.md` tasks are added via fragments.** To add a task, drop
a Markdown fragment in `todo.d/` (see `todo.d/README.md`) rather than editing
the `## 📥 Inbox` section of `TODO.md`, so parallel PRs never collide on the
TODO list. `scripts/assemble_todo.py` folds fragments in and deletes them, run
daily by `.github/workflows/todo-collect.yml`. This is **add-only**: checking a
task off, deleting it, or promoting it out of the Inbox into a curated section
is a normal direct edit of `TODO.md`.

## 🚧 Worktree Discipline (MANDATORY)

- **NEVER** edit files directly in the main working tree.
- **ALWAYS** create a worktree + feature branch before any code or workflow
  change: `git worktree add .worktrees/<branch-name> -b <branch-name>` (this
  repo's own history already uses `.worktrees/<branch>` — keep using it rather
  than inventing a second convention).
- **NEVER** commit directly to `main` — all changes go through PRs.
- If you catch yourself editing `main`, **STOP immediately**, move the changes
  to a worktree, and reset `main`.

**Before any edit:** run `git worktree list` to confirm where you are. If you're
in the primary checkout (`main`), create a worktree first.

**After the PR merges:** remove the worktree immediately —

```bash
git worktree remove .worktrees/<branch>   # or the full path
git worktree prune                         # cleans up any stale refs
```

Never leave a merged worktree sitting around — `git worktree list` should stay
short.

**Why:** this repo publishes the reusable workflows
(`.github/workflows/reusable-*.yml`) that every `falkcorp` repo's CI depends on
— a bad edit here breaks CI everywhere at once, not just locally. Direct commits
to `main` also collide with concurrent work; this repo has already had unrelated
staged changes sitting on `main` in the same file at the same time. This is
non-negotiable — no exceptions.

## 🔧 Git Operations Policy

**Preferred order for git operations:**

1. **MCP GitHub tools** (preferred) - Use when available
2. **safe-ai-util** (fallback) - Provides safety checks and logging
3. **Native git** (last resort) - Use only when other options unavailable

**Use VS Code tasks for non-git operations only** (build, lint, test, generate).

## 📋 Key Instruction Categories

### Workflow & Process

- Commit messages (conventional commits format)
- Pull request descriptions
- Code review guidelines
- Test generation standards
- Security best practices

### Language-Specific Rules

- Go, Python, TypeScript, JavaScript, Rust, Shell
- Protobuf, Markdown, JSON, JSONC, HTML/CSS
- GitHub Actions workflows

### Specialized Prompts

- Code review, documentation generation
- Bug reports, feature requests
- Merge conflict resolution
- Test generation

> For all Claude, Copilot, or workflow tasks, **refer to the files in
> `.github/instructions/` and `.github/prompts/`**.
