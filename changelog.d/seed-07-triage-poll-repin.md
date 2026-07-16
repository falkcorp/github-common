### Fixed

#### `reusable-triage-poll.yml` — re-pinned to a valid image tag; auto-updater now covers it too

`reusable-triage-poll.yml` was pinned to
`ghcr.io/falkcorp/burndown-runner-image:d558a3367025991ebe86e43e46b4d9f73da39b88`,
a tag that no longer existed in the registry (`docker pull` →
`manifest unknown`) — every 30-min triage-poll cron run failed at the image-pull
step, silently starving the pipeline of triaged tasks for an unknown duration.
Root cause: `burndown-runner-image`'s release workflow auto-updates the image
pin in `reusable-burndown.yml` on every image release, but never touched
`reusable-triage-poll.yml`, so this file's pin was guaranteed to drift stale as
soon as any newer image shipped. Re-pinned to `ob-20cdfe3` (verified live) and
extended the auto-updater's `PINNED_FILES` list
(`falkcorp/burndown-runner-image@330037a`) so future releases keep both files in
sync.
