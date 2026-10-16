### Fixed

#### Fallback workflow-scripts pin moved to `1f0d70e`, so repos without `ghcommon-ref.txt` get capped, file-based release notes

Every reusable workflow that checks out this repo's scripts, when the caller has
no `.github/ghcommon-ref.txt`, fell back to `e73b801`. That commit predates
github-common#374, so `reusable-release.yml` at `main` used its legacy inline
changelog path for those callers. That path is uncapped and passed through env,
so a long changelog still hit "Argument list too long". All 12 occurrences
across 6 workflows now point at `1f0d70e`, the #374 merge. The only script
change between the two commits is `release_workflow.py` from #374.
