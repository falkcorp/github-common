### Fixed

#### `assemble_todo.py` is now formatted identically at any ruff line-length

`ruff format` is not idempotent across line-lengths: a file formatted at 80
columns gets its short lines rejoined at 88. The assembler is copied verbatim
into repos that have no `ruff.toml` of their own, where ruff falls back to its
88-column default — so `ruff format --check` failed there even though the file
was correctly formatted for this repo.

Every multi-line construct now carries a magic trailing comma (which pins it
exploded at any width), and the two constructs that could not take one were
reshaped to fit under 79 columns. Verified byte-identical output at widths 79,
80, 88, 100, 120 and 200, and the file passes `ruff check`/`ruff format --check`
under both this repo's config and a bare `--isolated` default.
