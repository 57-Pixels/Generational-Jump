# Manufacturing / cost appendix — [program name]

> Optional deep-dive companion to a design doc when the industrial half is too long for one file.
> **Program id:** [must match `data/programs.csv`]
> **Parent design doc:** [link]

## 1. Plant and footprint

- Site, floor area, power, environmental constraints
- Retool of legacy plant vs greenfield
- Security / hardening notes

## 2. Process flow

Ordered station list (must match `data/production-lines.csv`). Diagram welcome.

## 3. Bill of materials narrative

Walk the critical path materials; cite `data/bom.csv` part_ids. Call out single-source imports.

## 4. Workforce and training

Roles, headcount by year, where people come from, how long until the second shift is competent.

## 5. Cost build-up

Derive the CSV unit costs from materials + labor + scrap + opex allocation. Show assumptions. Tag confidence per `industry/01-costing-method.md`.

## 6. Surge and wartime continuity

What changes on day 1 of a blockade or mobilization: overtime, substitute materials, mothballed cells, license wartime-continuation clauses.

## 7. Open risks

Unresolved industrial risks that block a `decided` status on the parent design doc.
