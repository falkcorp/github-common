### Changed

#### Go standards modernized to 1.26, with new test-isolation rules

`go.instructions.md` raises the mandatory minimum from 1.23 to 1.26 and
replaces the pre-1.24 idioms it was still presenting as current: the
`wg.Add(1)`/`defer wg.Done()` pair becomes `wg.Go`, the `errors.As` two-step
becomes `errors.AsType[T]`, `sort.Slice` on a typed slice becomes
`slices.SortFunc`, and four remaining `interface{}` become `any`.

The substantive addition is a testing section covering three things that
repeatedly cost real debugging time in adopting repos:

`testing/synctest` is a goroutine-isolation bubble, not merely a fake clock. A
`time.Sleep` used to wait for background work is an undecidable version of "did
it finish?", and its usual failure is not a red test — it is a timeout constant
that creeps upward over the years because a *correct* implementation keeps
losing a race with the assertion on a loaded runner. A budget that has been
raised more than once is a defect report, not a tuning parameter. The section
states the boundary too: do not convert a sleep standing in for real I/O, a
subprocess, or a database fsync, because a virtual clock does not make those
faster and the conversion hangs rather than passing.

Go isolates the environment (`t.Setenv`), the working directory (`t.Chdir`),
the filesystem (`t.TempDir`, `os.Root`) and lifetime (`t.Context`) — but it has
no isolator for package-level state. A function that reads a global cannot be
handed a different one by a test, and a caller that forgets to configure it
gets zero values and a silently disabled guard. Taking the dependency as a
required parameter turns that omission into a compile error.

`omitempty` and `omitzero` are not synonyms under `GOEXPERIMENT=jsonv2`: v2
emits `false` and `0` for `omitempty`, changing the wire shape of every bool
and numeric field that relied on v1 behaviour. The version-requirements block
now also states that a project opting into JSON v2 must set the experiment flag
on every build path — a local `.envrc` is not sufficient, since a CI or Docker
builder that misses it compiles different marshalling behaviour than the one
that was tested.

The branch-version-strategy block (the `stable-1-go-1.23` branch names and the
`workflow-versions.yml` matrix) is deliberately untouched: bumping those renames
branches that may exist, which is a separate decision.
