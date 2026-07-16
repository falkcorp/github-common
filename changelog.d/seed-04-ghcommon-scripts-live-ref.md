### Fixed

#### `reusable-release.yml` — ghcommon-scripts checkout used a live ref lookup that hit a GitHub Actions-side stale-resolution bug

Two of the three "Determine ghcommon workflow ref" steps derived the ref via
`${GITHUB_WORKFLOW_REF##*@}`, which in a reusable-workflow context extracts the
_calling_ repo's ref (e.g. `refs/heads/main`) rather than a ref specific to
`falkcorp/github-common`. That value happens to also be a valid branch name in
`github-common`, so it looked correct — but `actions/checkout`'s resolution of
`refs/heads/main` for this specific (recently renamed) repo consistently
returned a commit SHA that doesn't exist in either repo, reproducibly failing
every release with `fatal: could not fetch <sha> from promisor remote` even
though `git ls-remote` against the same ref from outside GitHub Actions resolves
correctly. Unified all three occurrences to the file-based lookup the third one
already used (read `.github/ghcommon-ref.txt`, falling back to a hardcoded SHA)
and added that file, pointing at the current commit — this sidesteps live ref
resolution entirely rather than depending on whatever caching layer produced the
bad SHA.
