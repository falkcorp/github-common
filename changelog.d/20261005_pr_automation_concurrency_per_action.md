### Fixed

#### pr-automation: an edit or label no longer cancels the run for the same commit

- The concurrency group now also includes `github.event.action`. Editing a PR body seconds after a push cancelled the push's `synchronize` run (seen on #365: Code Quality Check, Auto Label PR and AI Rebase stayed red as "cancelled" on the head commit even though the later run passed them). A new push still supersedes the previous push's run.
