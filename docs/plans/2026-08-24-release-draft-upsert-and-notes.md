<!-- file: docs/plans/2026-08-24-release-draft-upsert-and-notes.md -->
<!-- version: 1.0.0 -->
<!-- guid: 6f0b2a41-9c3d-4e18-8a75-2b1c4d90e7a3 -->
<!-- last-edited: 2026-08-24 -->

# Release-pipeline repair: duplicate drafts, flat notes, RC-based diff base, skipped release job

## Goal

Four defects, all surfaced by "why do I have 5 draft releases for v0.218.1 and why
aren't the notes grouped". Approved scope: all four.

## Evidence (all verified, not inferred)

| #   | Defect                                 | Proof                                                                                                                                                                                                                                           |
| --- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Draft upsert can't see existing drafts | `gh release list --json tagName,isDraft` has no `--limit` → gh default 30. Run against audiobook-organizer: returns **0** drafts while `gh api --paginate` returned **5**. Line 686, present at the pinned SHA `d0c3326b` and at `origin/main`. |
| 2   | Draft body is a flat commit dump       | `release_workflow.py::generate_changelog` emits `### 📋 Commits since vX:` + one bullet per commit. No grouping, never had any (v0.216.0, April, identical shape).                                                                              |
| 3   | Stable notes diff from an RC           | `v0.219.0` body: `compare/v0.218.1-rc.181...v0.219.0`, 2 entries total. `.goreleaser.yml` uses `{{ .PreviousTag }}`, which is the previous _git tag_ — an RC.                                                                                   |
| 4   | Release job skipped since ~Aug 18      | `Build Python Components: failure` (`pytest: command not found`, exit 127) → `create-release` has `if: always() && !failure()` → **skipped**. No draft and no RC from those runs.                                                               |

### Why #4 happens, in full

- `pyproject.toml` exists in audiobook-organizer but contains **only `[tool.black]`** — a
  formatter config, not a Python package. Detection keys on file existence → `has-python=true`.
- The caller cannot turn it off: line 195 is
  `python-enabled: ${{ inputs.python-enabled && 'true' || 'auto' }}`.
  A boolean `false` collapses to `'auto'`, which re-enables auto-detection.
  **`false` is unreachable for all six language flags.** This is the same bug the
  audiobook-organizer `prerelease.yml` comment already documents for `docker-enabled` —
  that comment is accurate, and this is the line behind it.
- `gha-release-python` defaults `run-tests: true`, `test-command: pytest …`; pytest is
  never installed → 127.

## Files to change

### A. `falkcorp/github-common` — worktree `.worktrees/release-draft-fix`, branch `fix/release-draft-upsert`

1. `.github/workflows/reusable-release.yml` — step "Create or update draft full release" (≈673-733)
   Replace tag-keyed `gh release list` logic with id-keyed paginated `gh api`.
2. `.github/workflows/reusable-release.yml` — lines 194-200, language override plumbing
   Make the six `*-enabled` inputs tri-state so `false` actually disables.
3. `.github/workflows/reusable-release.yml` — new step before the Go build
   Export `GORELEASER_PREVIOUS_TAG` = previous **stable** tag, stable cuts only.
4. `.github/workflows/scripts/release_workflow.py::generate_changelog`
   Group commits by conventional-commit type.

### B. `jdfalk/audiobook-organizer` — worktree `.worktrees/release-pipeline`, branch `fix/release-pipeline-notes`

5. `.github/workflows/prerelease.yml` + `.github/workflows/release-prod.yml`
   Bump the `github-common` pin to the merged SHA from (A); set `python-enabled: 'false'`;
   replace the stale `docker-enabled` comment with the real explanation.

## Ordered steps

1. **(A2) tri-state language flags first.** Everything else in A is additive; this one changes
   an input contract, so it goes in first and alone in its commit for a clean revert.
   - `type: boolean, default: false` → `type: string, default: 'auto'` for the six flags.
   - Line 195 pattern → `${{ inputs.python-enabled || 'auto' }}`.
   - Back-compat: a caller passing YAML `true`/`false` to a string input is coerced to
     `"true"`/`"false"`, both of which `_normalize_override` already accepts. Callers that
     omit the input get `'auto'` — today's behaviour. **No caller changes shape.**
2. **(A1) draft upsert by id.** Enumerate `gh api repos/$GITHUB_REPOSITORY/releases --paginate`,
   filter `.draft == true`, partition by `tag_name`:
   - same tag as `FULL_VERSION` → keep the newest by `created_at`, `PATCH` it, `DELETE` the rest;
   - different tag → `DELETE` (existing intent: stale drafts for superseded versions).
     All by numeric id. `gh release edit/delete <tag>` is ambiguous with duplicate tags and must not
     be used here.
3. **(A4) grouped changelog.** See "Open decision" below.
4. **(A3) `GORELEASER_PREVIOUS_TAG`.** Compute `git tag -l 'v*.*.*' --sort=-v:refname`, drop
   `-rc/-alpha/-beta`, take the newest strictly below the tag being cut; export to `$GITHUB_ENV`
   **only when `release-branch-strategy == 'stable'`** — for an RC, diffing against the previous
   RC is correct and must not change.
5. **(B5)** after A merges: bump pin, set `python-enabled: 'false'`, fix the comment.

## Test strategy

- `actionlint` on the changed workflow.
- Python: unit-test `generate_changelog` against a fixture commit list — assert every input commit
  appears in exactly one group, and that a `feat(x)!:` breaking-change subject lands in Features.
- **Instrument check (a bogus value):** run the new draft-enumeration jq against a synthetic
  releases JSON containing 40 prereleases + 2 same-tag drafts and assert it finds **2**. The old
  code finds 0 on the same input — that difference is the regression test.
- Dry-run the previous-stable-tag resolver against audiobook-organizer's real tag list; expected
  `v0.219.0` → `v0.218.1`, **not** `v0.218.1-rc.181`.
- End-to-end: after the pin bump, the next merge to audiobook-organizer main must produce exactly
  one `v0.219.1` draft, and a second merge must leave it at exactly one.

## Rollback

- A2 is the only contract change: revert that commit and callers return to boolean semantics.
- A1/A3/A4 are self-contained steps; reverting any one leaves the others working.
- B5 rollback is a one-line pin revert to `d0c3326b`.
- The 5 orphaned drafts were already deleted (verified 0 remaining); nothing to roll back there.

## Open decision — needs the user

`generate_changelog`'s grouping taxonomy. `.goreleaser.yml` **excludes** `docs:`, `test:`,
`chore:` entirely. Mirroring that makes the draft match the stable release exactly, but silently
drops commits from the draft — and the draft is the thing being reviewed before publishing.
Keeping them in a low-priority group is more honest but diverges from the stable notes.
