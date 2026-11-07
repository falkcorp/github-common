### Changed

#### `reusable-release.yml` — release tag push and changelog commit can run as the CI bot GitHub App

`build-go` (release tag push) and `collect-changelog` (changelog commit) now
authenticate as the CI bot GitHub App when the caller provides one. A new
optional input `ci-bot-app-client-id` (falling back to the caller's
`CI_BOT_APP_CLIENT_ID` variable) and optional secret `CI_BOT_APP_PRIVATE_KEY`
select it; the legacy `CI_APP_ID` / `CI_APP_PRIVATE_KEY` pair keeps working for
consumers that have not moved, and a caller with neither behaves as before. Both
jobs declare `environment: ci-bot`, so the key can be held as an environment
secret limited to the default branch. A half-configured pair is an error,
except on `pull_request` runs where secrets are withheld. Both mints are
narrowed with `permission-*` inputs.

#### `reusable-release.yml` `build-go` — the app token is now actually used for the tag push

The token was minted but never used: checkout persisted `GITHUB_TOKEN` as
`http.extraheader`, and git sends that header in preference to the token
embedded in the push URL. Checkout now takes the app token, so the persisted
credential and the tag push agree.

#### `reusable-release.yml` `collect-changelog` — direct push tries the app first

The direct push to the default branch now prefers the app token, then the PAT,
then `GITHUB_TOKEN`. Previously the app was used only for the fallback pull
request, so a ruleset bypass naming the app never helped and every collect fell
through to the pull request. The commit carries the app's bot identity, resolved
at runtime.
