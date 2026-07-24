# Industry Overview

> **Status:** framework — this folder is the industrial half of every design decision.
> Platforms live in `designs/`. Factories, materials, and cost logic live here and in `data/*.csv`.

## Premise (locked direction)

We are running a **full generational jump** from an 80s–90s force to a modern one across **every domain**. That is not a shopping list — it is an industrial program. Every major platform decision must answer:

1. What are we building?
2. What is it made of, and where do those materials come from?
3. What does the assembly line look like?
4. What does a unit cost at ramp and at rate?
5. What breaks if the port closes or a supplier cuts us off?

## How industry docs relate to CSVs

| Question | Doc | Data |
| --- | --- | --- |
| What programs exist? | design docs in `designs/` | `data/programs.csv` |
| What does it cost? | design doc § Cost model | `data/cost-estimates.csv` |
| What is it made of? | design doc § Materials / BOM | `data/bom.csv` |
| How is it built? | design doc § Production line + `industry/` plant notes | `data/production-lines.csv` |

Markdown argues. CSV stores the numbers a future website will chart.

## Key questions for the national industrial base

1. **Which plants already exist**, and what 80s–90s products do they make today?
2. **Which plants must be built or heavily retooled** for the generational jump?
3. **Critical materials** we cannot source domestically (propellants, specialty alloys, microelectronics, jet-engine hot-section metals).
4. **Workforce:** machinists, welders, avionics techs, shipyard trades — training pipeline length vs. program schedule.
5. **Shared tooling** across programs (e.g. one barrel forge serving rifles *and* machine guns) — conflicts become design constraints.

## Starter suggestions

> **[STARTER SUGGESTION]** — overwrite freely; promote to `decisions-log.md` when canon.

- **Existing plants (legacy era):** one small-arms/ammo complex, one truck/assembly plant, one shipyard that builds patrol craft and repairs freighters, one airframe MRO hangar that cannot build fighters, one artillery/armor plant idle at ~30% capacity on legacy overhauls.
- **Near-term retool targets (years 1–5 of modernization):** small-arms line (worked example), truck militarization line, ammo surge cells, coastal-missile boat line.
- **Greenfield / heavy lift (years 5–15):** fighter final-assembly (if licensed), major surface combatant modules, SAM seeker/electronics partnership.
- **Shared constraint:** precision CNC capacity and heat-treat capacity are national bottlenecks — schedule programs so they do not all peak in the same year.
