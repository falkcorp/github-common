### Changed

- **bootstrap-repo no longer applies classic branch protection.** Branch rules come
  from the org-wide rulesets. `apply_branch_protection.sh` and
  `discover_status_checks.py` are deleted, and `--skip-protection` is gone.
  `verify_bootstrap.sh` now treats the *presence* of classic protection as drift.

### Fixed

- Classic protection has no `bypass_actors`, so it blocked the `Sync from Template`
  bot from pushing to `main` in 15 `gha-*` repos for ~4 months (GH006). Adding
  bypasses to the org rulesets had no effect, because classic protection does not
  consult them.
- The required contexts the skill installed were **job IDs**, but GitHub reports
  status checks by **display name** (`test-with-config` vs `Test With Valid Config`),
  so they were never satisfied and every PR sat blocked — 34 Dependabot PRs were
  unmergeable, some for over six months.
- Autodiscovery also made `set-auto-merge` a required check. That job is gated on
  `if: contains(labels, 'auto-merge')`, so it is *skipped* without the label, and a
  skipped required check never satisfies protection — a silent permanent deadlock.
- `verify_bootstrap.sh` tested `gh api` output rather than its exit status. `gh api`
  prints HTTP error bodies to **stdout**, so a 404 still produced a non-empty string
  and the protection check could never detect the absent case.
