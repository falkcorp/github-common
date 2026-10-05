### Fixed

#### pr-automation: pull_request and pull_request_target runs no longer cancel each other

- The concurrency group now includes `github.event_name`. Every PR event fired both a `pull_request` and a `pull_request_target` run into the same group, so the second one cancelled the first and left its jobs (Code Quality Check, Auto Label PR, PR Analysis, Breaking Changes Check, AI Rebase, Intelligent AI Labeling) as red "cancelled" checks on every PR, including dependabot's #363 and #364.
