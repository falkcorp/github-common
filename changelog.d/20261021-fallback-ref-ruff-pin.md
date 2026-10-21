### Changed

- `reusable-ci.yml`: the fallback ghcommon script ref (used when a caller has no
  `.github/ghcommon-ref.txt`) now points at `861d4e83`, so callers without a pin
  get the ruff 0.17.0 Python lint from #378.
