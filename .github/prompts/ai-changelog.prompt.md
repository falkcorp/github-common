<!-- file: .github/prompts/ai-changelog.prompt.md -->
<!-- version: 2.0.0 -->
<!-- guid: 253c622c-7e27-41ad-99f9-d81791d6b251 -->
<!-- last-edited: 2026-07-16 -->

# AI Changelog Generation Prompt

`CHANGELOG.md` is **assembled** from fragments — do **not** edit it directly.
For every change worth recording, add a changelog fragment under `changelog.d/`.
Editing `CHANGELOG.md` by hand causes merge conflicts across parallel PRs, and a
CI check fails any PR that changes code without a fragment.

## How to add a fragment

- Run `scriv create` (writes `changelog.d/<timestamp>_<branch>.md`), or create a
  Markdown file there by hand following `changelog.d/README.md`.
- Group entries under Keep a Changelog categories: `Added`, `Changed`,
  `Deprecated`, `Removed`, `Fixed`, `Security`.
- Map from the conventional-commit type: `feat` → Added, `fix` → Fixed,
  `perf`/`refactor` → Changed; deprecations/removals/security as named.
- A changelog entry carries **more detail than a release note**: give each entry
  a `#### short title` and an explanatory paragraph covering what changed, why,
  and any impact or reproduction — mirror the existing entries in
  `CHANGELOG.md`.
- Do **not** add a file header to fragment files (it would leak into the
  changelog). One fragment per logical change; the filename is unique so
  fragments never conflict.

## Guidelines

- Reference the
  [general coding instructions](../instructions/general-coding.instructions.md)
  and the relevant language/framework `.instructions.md` file in
  `.github/instructions/`.
- Use clear, concise language and Markdown formatting.
- Link to related issues, PRs, and documentation where useful.

Assembly into `CHANGELOG.md` happens automatically at release time via
`.github/workflows/changelog-collect.yml` (`scriv collect`); GitHub release
notes remain commit-based and separate.
