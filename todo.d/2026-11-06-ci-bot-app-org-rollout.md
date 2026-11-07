- [ ] **TODO-CI-BOT-APP** Move every falkcorp bot push and bot PR to the org CI bot GitHub App
      (org var `CI_BOT_APP_CLIENT_ID`, org secret `CI_BOT_APP_PRIVATE_KEY`). Personal app
      3382666 (`CI_APP_*`) and the `JF_CI_GH_PAT` PAT both get retired. Order:
  - [ ] `reusable-release.yml`: collect-changelog pushes with the minted app token first
        (today it mints one but pushes with the PAT or GITHUB_TOKEN → GH013 on merge-queue repos).
        build-go checkout gets `persist-credentials: false` so checkout's extraheader can't
        override the app token. Mints switch to `client-id`, narrowed per job.
  - [ ] Reusable workflows default to `CI_BOT_*`, so a downstream repo migrates by bumping
        its github-common pin, with no per-repo token code.
  - [ ] github-common's own PAT users move off it: `todo-collect`, `sync-repos`,
        `reusable-burndown` (its ghcr login needs `packages: read`, not the app),
        `sync-dispatch-events.py`, `monitor-rollout.py`.
  - [ ] Per repo, as it migrates: add it to the app installation and to the secret/var
        repo lists (selected repos, not "all"). If it has a merge-queue ruleset, the app
        becomes that ruleset's only bypass.
  - [ ] Org rulesets: Linear History lists the old app as bypass. Swap in the new app
        wherever a bot pushes to a protected branch.
  - [ ] Repos still on `CI_APP_*`: migrate-loop, gha-release-go, gha-release-docker,
        gha-release-frontend (plus audiobook-organizer and github-common).
        Repos still on `JF_CI_GH_PAT`: apt-cacher-go, gcommon, subtitle-manager,
        ubuntu-autoinstall-agent.
  - [ ] Retire last, after a green week with no readers: delete `CI_APP_*`, uninstall and
        delete app 3382666, revoke `JF_CI_GH_PAT` and delete the org secret.
