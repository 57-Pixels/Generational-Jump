# [Equipment name / program name]

> **Domain:** logistics / soldier-systems / c4isr / land / air / sea
> **Status:** draft / decided / superseded by [link]
> **Program id:** [must match `data/programs.csv`]
> **Drives episode(s):** [link(s)]
> **Decision logged:** [link to decisions-log.md entry, or "pending"]

This template covers **both halves** of a decision: the operational design *and* the industrial design (materials, line, cost). Surface-level "buy platform X" writeups are not enough for this series.

---

## A. Operational design

### 1. Requirement

What operational problem does this solve? State it as a problem, not a product.

- **Traces to scenario(s):** [link]
- **Legacy baseline:** what 80s–90s system this replaces (or supplements)
- **What happens if we don't solve it:**
- **Quantity and timeline:** how many, fielded by when

### 2. Constraints

Every constraint links to the world bible or industry docs. If it isn't written down, write it there first.

| Constraint | Value | Source |
| --- | --- | --- |
| Budget / annual affordability | | `world/03`, `data/cost-estimates.csv` |
| Industrial capability | design / license-build / assemble / import | `industry/00-overview.md` |
| Geography and climate | | `world/01-our-nation.md` |
| Manpower and training | | `world/01-our-nation.md` |
| Import / supplier politics | | `world/04-alliances-and-diplomacy.md` |

### 3. Options considered

Three to five options. Include a cheap option and a gold-plated option. Steelman each.

#### Option A: [name]

- **Real-world analogue:**
- **Industrial path:** import / license / domestic design
- **Rough unit cost at rate + tooling capex:** (point at CSV rows once estimated)
- **Pros / cons / fit:**

#### Option B / C / … — same structure

### 4. Decision and rationale

One sentence pick, then the chain from constraints → choice. Must be specific to *this* country.

### 5. Rejected alternatives

Answer "why not just X?" for the obvious objections. This section *is* the video argument.

### 6. Second-order effects

Logistics tail, training, doctrine, industrial side-effects, follow-on programs triggered.

---

## B. Industrial design

Skip this half only for pure doctrine docs. For any hardware program, fill it.

### 7. Materials and BOM

- **BOM lives in:** `data/bom.csv` filtered on `program_id=…`
- **Critical import lines:** [list part_ids]
- **Stockpile / surge notes:** link to `industry/02-materials.md`
- Narrative summary of material risks the CSV cannot express.

### 8. Production line

- **Line lives in:** `data/production-lines.csv` filtered on `program_id=…`
- **Plant:** existing retool / greenfield (link `industry/00-overview.md`)
- **Design rate:** units/year
- **Bottleneck station:** [station_name]
- **Workforce:** peak operators across shifts; training lead time
- Narrative: how the line is laid out and what fails first under surge.

### 9. Cost model

- **Method:** `industry/01-costing-method.md`
- **Rows:** `data/cost-estimates.csv` for this `program_id`
- **Headline numbers for episodes:**
  - Tooling + facility capex:
  - Unit cost year-1 vs rate-year:
  - Program total through IOC quantity:
- **Confidence:** order-of-magnitude / study-grade / quote-analogue / line-model
- Show the comparison table that killed the rejected options (same confidence for each).

### 10. Data checklist

Before marking status `decided`:

- [ ] Row in `data/programs.csv`
- [ ] BOM rows in `data/bom.csv`
- [ ] Line rows in `data/production-lines.csv`
- [ ] Cost rows in `data/cost-estimates.csv`
- [ ] Decision logged in `decisions-log.md`
