### Security

#### Force `brace-expansion` >= 5.0.7 via npm override (last open Dependabot alert)

Added a `brace-expansion` npm `overrides` entry (matching the existing lodash/js-yaml/fast-uri
pattern) to force the transitive dev dependency to a patched 5.0.7. It was pinned at 5.0.6 under
`@typescript-eslint/typescript-estree`; Dependabot's security-updater could not bump it
("update_not_possible: downgrades_dependencies"). `npm` now reports 0 vulnerabilities.
