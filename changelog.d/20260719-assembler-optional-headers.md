### Fixed

#### `assemble_todo.py` no longer aborts when the output file lacks a header line

`bump_header` raised and failed the whole collect if `TODO.md` had no
`version:` or `last-edited:` line. That is fine in this repo, where both are
always present, but wrong across a fleet: several adopting repos have a
`version:` line and no `last-edited:` (transcoderr, for one), so their first
scheduled collect would have failed with nothing to do about it.

Header upkeep is now best-effort — each line is refreshed only if present, and a
missing one is a warning rather than an error. Adding tasks is the job; header
maintenance must never be the reason a scheduled collect fails. Genuinely unsafe
conditions (a missing insert marker, a missing output file) still raise.
