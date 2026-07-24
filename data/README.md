# data/

Simple, structured numbers for the project. Markdown holds reasoning; these CSVs hold figures a future website can load into tables and charts. Kept intentionally light — industry/cost detail is a supporting thread, not the focus.

## Files

| File | Purpose |
| --- | --- |
| `programs.csv` | Index of every program |
| `costs.csv` | One rough cost line per program (setup, per-unit, total) |

## Conventions

- **IDs** (`rifle-std-1`) are stable forever; never reuse for a different thing.
- **Currency:** project-dollars (`PD`) ≈ 2025 USD.
- **Costs are rough estimates** — often AI-generated. Tag confidence as `rough`, `study`, or `firm` in `costs.csv`.
- Column names are snake_case and stable; treat renames as breaking changes and note them in `decisions-log.md`.

A future site can read these CSVs directly or transform them to JSON.
