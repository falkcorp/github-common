### Changed

#### `reusable-release.yml` `collect-changelog` — direct push tries the CI bot app first

The changelog commit can now be pushed as the CI bot GitHub App. The direct push
to the default branch prefers the app token, then the PAT, then `GITHUB_TOKEN`.
Previously the app was used only for the fallback pull request, so a ruleset
bypass naming the app never helped and every collect fell through to the pull
request. The commit carries the app's bot identity, resolved at runtime. New
optional input `ci-bot-app-client-id` (falling back to the caller's
`CI_BOT_APP_CLIENT_ID` variable) and optional secret `CI_BOT_APP_PRIVATE_KEY`
select the bot app; the legacy `CI_APP_ID` / `CI_APP_PRIVATE_KEY` pair keeps
working, and a caller with neither behaves as before. The legacy secrets and
`JF_CI_GH_PAT` are now declared as optional `workflow_call` secrets, which
declaring any secret requires.

#### `reusable-release.yml` — the bot app key is opt-in through a caller environment

New input `bot-environment` (default empty). The `collect-changelog` job runs in
the environment it names, so only a caller that holds the key as that
environment's secret can use the bot app; every other consumer runs outside any
environment and is unchanged. Outside an environment a client id without a key
is treated as "no app" with a warning, not an error. `build-go` is deliberately
untouched: it keeps the default `GITHUB_TOKEN` checkout.

#### `reusable-release.yml` `collect-changelog` — scriv runs without credentials

The job is split so the step that installs and runs scriv (pinned to `1.8.0`)
has no token in its environment. The app token, PAT and `GITHUB_TOKEN` reach
only a separate step that re-verifies the single changelog commit (only
`CHANGELOG.md` and `changelog.d/` touched) and then pushes or opens the pull
request.
