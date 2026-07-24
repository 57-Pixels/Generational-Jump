# data/

Structured quantitative data for the project. Markdown docs hold *reasoning*; CSVs hold *numbers* a future website can load into tables, charts, and cost calculators without parsing prose.

## Files

| File | Purpose |
| --- | --- |
| `programs.csv` | Index of every equipment / industrial program |
| `cost-estimates.csv` | Capex, unit cost, and opex by program and year |
| `bom.csv` | Bill of materials / critical materials per program |
| `production-lines.csv` | Assembly-line stations, cycle time, workforce, tooling |

## Conventions

- **IDs** are stable forever (`rifle-std-1`). Never reuse an id for a different thing.
- **Currency** is project-dollars (`PD`) — fictional, but treated like USD for 2025 purchasing power. Column `currency` is always `PD` unless noted.
- **Costs are estimates**, not truth. Confidence lives in `notes` and in the linked design doc.
- **One row = one fact.** Prefer adding a year row over editing history away; superseded estimates get `status=superseded` and a newer row.
- Design docs that cite a number must point at a CSV row (program id + year), not invent a one-off figure.

## Website path

A future site can `fetch` these CSVs directly, or build a small ETL into JSON. Column names are snake_case and stable — treat renames as breaking changes logged in `decisions-log.md`.
