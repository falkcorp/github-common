### Fixed

#### `reusable-release.yml` — changelog collection silently stopped once fragments accumulated

The "are there any fragments?" guard was written as
`! find changelog.d ... | grep -q .` under `set -o pipefail`. `grep -q` exits on
the first match, closing the pipe; `find` then dies on `EPIPE`, and pipefail
reports the whole pipeline as failed even though grep succeeded. The leading `!`
turned that into "no fragments to collect" — firing precisely when there were
*many* fragments — and it `exit 0`s, so the release stayed green while the
changelog was never assembled.

It is a race that fragment growth makes near-certain rather than a fixed
threshold: `find` only loses if it is still writing when `grep` exits.
`audiobook-organizer` collected normally at 131 fragments (~7 KB of `find`
output), then silently skipped six consecutive releases at 675 (~36 KB),
accumulating a backlog that CI kept demanding additions to. The guard now uses
`find -print -quit`, which stops at the first hit and needs no pipeline at all.

Fixed the same EPIPE-under-pipefail hazard in the RC-number lookup, where
`git tag -l ... | head -1` would become a hard step failure once a version had
enough RC tags to outrun the pipe buffer.
