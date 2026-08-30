### Fixed

#### `reusable-release.yml` — the remaining EPIPE-under-pipefail pipelines, including a destructive one

The previous fix corrected the changelog-collection guard and the RC-number
lookup. Sweeping the rest of the file for the same shape — a producer piped into
a reader that exits early, under `set -o pipefail` — found four more, one of
which deletes releases.

**The destructive one.** The superseded-release cleanup spared keep-listed tags
with `printf '%s\n' "$keep_list" | grep -qxF "$tag"`. `grep -qxF` exits on the
first match; a still-writing `printf` then dies on `EPIPE`, and pipefail reports
the pipeline as failed *even though grep matched*. The `Keeping recent RC` branch
is skipped and the tag falls through to `gh release delete --yes --cleanup-tag`
— deleting a release the keep-list explicitly named. Not reachable at today's tag
counts (a few KB goes out in a single `write()`), but it is the identical shape
in the one code path that destroys artifacts, in workflows whose repos have
accumulated hundreds of RC tags.

Also converted: the `$base` version validation, the `sort -V | head -1`
smallest-version pick, the `echo "$MATCHING_IDS" | head -n1` draft-release lookup,
and `is_disabled()`'s normalisation pipeline (where an EPIPE would make a
*disabled* language read as enabled). Each becomes a here-string or a
capture-and-slice — a redirect rather than a pipe, so no stage can EPIPE.

Two sites are deliberately unchanged and are safe by construction: the
`LATEST_FULL` lookup ends in `|| true`, and the `scriv-insert-here` check has
`grep` read the file directly with no pipeline.

**The mechanism, measured.** It is a race, not a buffer-size threshold. A
reproduction with the original guard reports "no fragments" for a directory
holding 675 and 3000 files, and reports correctly at 13:

```
   13 files | OLD: fragments present | NEW: fragments present
  675 files | OLD: no fragments      | NEW: fragments present
 3000 files | OLD: no fragments      | NEW: fragments present
```

675 entries is roughly 53 KB of `find` output — comfortably under the 64 KB pipe
buffer — so a full buffer is not what breaks it. The writer dies only if it is
still writing when the reader exits: a few entries go out in one `write()` that
lands before the reader is scheduled, while hundreds mean many writes and the
reader almost always wins.
