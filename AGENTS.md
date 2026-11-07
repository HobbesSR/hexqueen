# HexQueen agent guide

HexQueen is a hexagonal queens logic puzzle: a Python generator and solver (`src/`, `run.py`) and
a dependency-free browser game (`web/`). `README.md` explains both.

## Checks

- Web engine tests: `node --test web/test/core.test.js`.
- Python tests: `python -m unittest discover tests`.
- Package for itch.io: `python run.py --package` writes `dist/hexqueen-web.zip`.

## Rules

- Keep `web/` dependency-free static files with relative paths, so it runs from any static host
  and inside itch.io's cross-origin iframe. Do not rely on the page URL (including `#codes`) or on
  storage being available; wrap storage access in try/catch.
- Before adding third-party code, fonts or assets, or a new dependency, check that its licence
  is compatible with the project's MIT licence, and record it with its notices
  ([docs/third-party-licenses.md](docs/third-party-licenses.md), `THIRD-PARTY-NOTICES.txt`).
  Escalate copyleft, non-commercial or unlicensed material; never add it without asking.
- `CLAUDE.md` only imports this file; edit this file, not it.
