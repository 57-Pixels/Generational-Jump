# Fantasy Military Design Project

A long-form **military design** project set in a fictional world at **2025 technology, no magic**. The country starts with an **1980s–1990s military**. A major conventional war **elsewhere** is the wake-up call. The mandate: a **full generational jump across every domain** — land, air, sea, C4ISR, soldier systems, logistics.

The focus is the **design reasoning** behind each choice. Industry and cost matter but are a **light supporting note** (rough, often AI-assisted) — not the subject. This repository is the source of truth for a video series. Markdown holds reasoning; **CSV holds a few numbers** a future website can load directly.

## How the documents connect

```
world/  →  maps/  →  threat-analysis/  →  doctrine/  →  industry/ + data/  →  designs/  →  episodes/
(bible)    (image-gen     (scenarios)        (jump)       (light costs)         (programs)   (videos)
            briefs)
```

## Reading order

1. [`world/00-world-overview.md`](world/00-world-overview.md) — planet, **pecking order**, Maravic wake-up war
2. [`maps/00-world-map-brief.md`](maps/00-world-map-brief.md) — **image-gen brief** for the world map (then upscale)
3. [`world/01-our-nation.md`](world/01-our-nation.md) — **Veldara** (mini-US scale) + legacy force
4. [`maps/01-country-maps-brief.md`](maps/01-country-maps-brief.md) — **multi-map** country set (political, physical, climate, infra, industry, military)
5. [`world/02-neighbors-and-threats.md`](world/02-neighbors-and-threats.md)
6. [`world/03-economy-and-industrial-base.md`](world/03-economy-and-industrial-base.md)
7. [`world/04-alliances-and-diplomacy.md`](world/04-alliances-and-diplomacy.md)
8. [`threat-analysis/00-threat-overview.md`](threat-analysis/00-threat-overview.md)
9. [`doctrine/00-national-defense-strategy.md`](doctrine/00-national-defense-strategy.md)
10. `designs/` — one design doc per program (reasoning + a short industry note)
11. [`episodes/00-series-outline.md`](episodes/00-series-outline.md)

## Directory guide

| Path | Contents |
| --- | --- |
| `world/` | World bible, pecking order, Veldara baseline |
| `maps/` | Image-gen briefs: world map + multi-type country maps |
| `industry/` | Light industry/cost notes (deliberately thin) |
| `data/` | Simple CSVs: `programs.csv`, `costs.csv` |
| `threat-analysis/` | Ranked threats and scenarios |
| `doctrine/` | Generational-jump strategy |
| `designs/logistics/` | Trucks, fuel, ammo, maintenance |
| `designs/soldier-systems/` | Rifles, optics, armor, kit |
| `designs/c4isr/` | Comms, networks, ISR |
| `designs/land/` | Artillery, armor, AT |
| `designs/air/` | Air defense and air force |
| `designs/sea/` | Navy |
| `episodes/` | Series outline and arcs |
| `templates/` | Design doc, episode, scenario |
| `decisions-log.md` | Canon log |

## Series order (a reorderable default)

Suggested boring → exciting: logistics → soldier systems → C4ISR → land → air defense → air force → navy → stress tests.

**Priorities and depth follow my interest and what I learn** — reorder, skip ahead, or double back freely. Each topic is as deep as it deserves; industry/cost is a short beat, not its own arc.

## Workflow for a new program

1. Trace the requirement to a scenario (or to the jump mandate).
2. Add a row to [`data/programs.csv`](data/programs.csv).
3. Copy [`templates/design-doc.md`](templates/design-doc.md); focus on the design reasoning.
4. Add a rough cost row to [`data/costs.csv`](data/costs.csv) and keep §7 (Industry) short.
5. Log the decision in [`decisions-log.md`](decisions-log.md).
6. Outline the episode under `episodes/`.

## Status labels

- **[STARTER SUGGESTION]** — proposed world defaults; not canon until logged.
- **[WORKED EXAMPLE]** — demonstrates the design reasoning and a light industry note (rifle program); replaceable.

## Worked example

- Design: [`designs/soldier-systems/infantry-rifle.md`](designs/soldier-systems/infantry-rifle.md)
- Data: `rifle-std-1` rows in `data/programs.csv` and `data/costs.csv`
- Episode: [`episodes/ep-soldier-rifle-arc.md`](episodes/ep-soldier-rifle-arc.md)
