# Branch Protection — do NOT apply classic protection

**This skill deliberately does not configure branch protection.** Branch rules for
falkcorp repos come from **org-wide rulesets**, not per-repo classic protection.

Until 2026-08-21 this skill ran `apply_branch_protection.sh`, which did a
`PUT /repos/{owner}/{repo}/branches/main/protection`. That script and its helper
`discover_status_checks.py` have been deleted. Do not reintroduce them.

## Why classic protection is harmful here

**1. It has no bypass list at all.** Org rulesets support `bypass_actors`, so
automation (apps, integrations, org admins) can be exempted. Classic protection
has no equivalent — `enforce_admins: false` does _not_ extend a bypass to a PAT or
a GitHub App token. Anything it blocks, it blocks for everyone, forever.

Measured: classic protection on 15 `gha-*` repos blocked the `Sync from Template`
bot from pushing to `main` for roughly four months.

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Changes must be made through a pull request.
```

Adding more bypass actors to the org rulesets did nothing, because the rejection
came from classic protection, which does not consult them. Deleting classic
protection fixed it on the next run.

**2. The contexts it installed could never be satisfied.** `discover_status_checks.py`
extracted **job IDs** from workflow files, but GitHub reports status checks by
their **display name** (`name:`), not the job ID. So the required contexts never
matched anything that reports:

| required context (job id) | what GitHub actually reports |
| ------------------------- | ---------------------------- |
| `test-with-config`        | `Test With Valid Config`     |
| `test-without-config`     | `Test With Missing Config`   |
| `validate`                | `Validate Action`            |
| `lint`                    | `Lint`                       |

Every such context sat in the "Expected" state permanently, so **every PR in those
repos was blocked** — 34 Dependabot PRs were unmergeable, some for over six months.

**3. It picked up conditional jobs as required checks.** `auto-merge.yml` has a job
`set-auto-merge` gated on `if: contains(labels, 'auto-merge')`. Autodiscovery made
it a _required_ check. With no label the job is **skipped**, and a skipped required
check never satisfies protection — a permanent, silent deadlock. The `auto-merge`
label did not even exist in any of the repos.

## What to do instead

Branch rules live in the org rulesets on `falkcorp` (Linear History, No Deleting
Main Branches, etc.), which carry `bypass_actors` for the automation that needs it.
If a repo needs a rule, add it there.

`verify_bootstrap.sh` now checks that classic protection is **absent** and reports
its presence as drift.

To remove it from a repo that still has it:

```bash
gh api -X DELETE "repos/${OWNER}/${REPO}/branches/main/protection"
```
