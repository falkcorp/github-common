### Changed

#### Extend Dependabot pip coverage to `/scripts` and `/scripts/copilot-firewall`

The pip `dependabot.yml` entry only scanned `/`, leaving `scripts/requirements-notifications.txt`
and `scripts/copilot-firewall/requirements.txt` without version/security-update PRs. Switched
`directory: /` to a `directories` list covering all three so every tracked pip manifest is updated.
