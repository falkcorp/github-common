### Fixed

#### `reusable-release.yml` — long release notes no longer fail the release with "Argument list too long"

The changelog was passed to `softprops/action-gh-release` through `body:`, and to
the RC draft step through an env var and `gh api -f body=` / `gh release --notes`.
Each of those puts the whole notes into a single env/argv string, which Linux caps
at 128 KiB. A stable release with hundreds of commits since the last tag
(audiobook-organizer v0.222.2, about 125 KB of notes) died in "Create GitHub
Release" after the release was already published. Every later step then skipped:
changelog fragment collection, the draft cleanup and the GitHub Packages publish.

`release_workflow.py generate-changelog` now writes the notes to a file
(`changelog_file` output) and caps the commit list at 110,000 characters, newest
first, ending with "… and N older commit(s) not listed". GitHub rejects release
bodies over 125,000 characters. The release step reads the notes with
`body_path:`, and the draft step uses `-F body=@file` / `--notes-file`.

`create-release` fetches the workflow scripts at the caller's
`.github/ghcommon-ref.txt`, or at the fallback SHA, separately from the
workflow, so the two can be at different versions. The script still emits
`changelog_content`, so an older workflow paired with this script keeps
publishing notes. In the other direction, both new steps stop with an
`::error::` naming the ref to bump instead of a bare `cat` failure. Callers
that set `ghcommon-ref.txt` must bump it together with the `uses:` pin.
