# World Overview

> **Status:** working world design.
>
> **Principles:** [`12-worldbuilding-principles.md`](12-worldbuilding-principles.md) · [`13-resources-from-geology.md`](13-resources-from-geology.md)  
> **Geology:** [`05-planetary-formation.md`](05-planetary-formation.md)  
> **Last 20 ka (Earth-analogue civ history):** [`08-last-20ka.md`](08-last-20ka.md) · [`09-historical-timeline.md`](09-historical-timeline.md) · [`10-classical-civilizations.md`](10-classical-civilizations.md) · [`11-legendary-figures.md`](11-legendary-figures.md)  
> **How countries form (grain → transport → borders):** [`06-settlement-and-borders.md`](06-settlement-and-borders.md)  
> **Pseudo-histories:** [`07-pseudo-histories.md`](07-pseudo-histories.md)  
> **Deep-time map:** [`../maps/generator/deeptime/`](../maps/generator/deeptime/)
## Ground rules (canon — see decisions-log)

- **Technology level:** Earth, 2025. No magic, no sci-fi.
- **Different world:** fictional geography and states; equipment by real-world *analogue*.
- **Physics and economics are real.**
- **Countries are earned:** food cores and transport spines first; borders are freeze-frames of that history.
- **Our starting force:** 1980s–1990s generation. Series = full generational jump, all domains.
- **Catalyst:** the **Maravic War** on Farreach.

## Continents vs landmasses

**Plate = current rigid kinematic domain. Continent = continental-crust/terrane lineage. Landmass = continuous dry land.** These overlap but are not aliases. Present land fraction is **emergent** from crust history (no clamp). The **promoted algorithmic seed 150** measures ≈ **44%** land; the older ellipse reference-campaign board was authored near Earth ≈ 29%. See [`12`](12-worldbuilding-principles.md) and `maps/generator/promoted-seed.json`.

| Name | Kind | Role (reference campaign / seed 150) |
| --- | --- | --- |
| **Aurelian** | Continent lineage (mostly one present plate) | Home board — Veldara, Korvath, Doverin, Sereth + footnotes |
| **Kharzhan** | Continent lineage (mostly one present plate) | Great-power homeland across the East Ocean rift |
| **Nerath** / **Tesen** | Continental lineages + present plates | Colliding under the **Farreach** landmass — Maravic War |
| **Farreach** | **Landmass** (not one plate) | Sutured Nerath + Tesen; one dry board, two continents |
| **Solmar** | Continental fragment lineage | Solara homeland + arc islands (Australia-scale) |

**Canonical generator:** `python3 -m deeptime --engine v2 --seed 150` (`GENERATOR_VERSION` 2.2.0). Politics: `06`/`07`. Ellipse shapes in `05` remain the formation *story*; coordinates for new work come from the promoted seed.
## Who is on stage vs footnote

**Fuller history** for: **important/neighbors**, **odd ones out** (improbable leftovers), and **countries of interest**. Detail still scales with recency ([`12`](12-worldbuilding-principles.md)).

**On stage** (default fuller set): Veldara, Korvath, Doverin, Sereth, Solara, Kharzhan State, Nerath Compact, Tesen League, Iberon Union (thin), plus named odd-ones-out when they explain a chokepoint/buffer/clerical fossil.

**Footnotes** (name + one line): see bottom of `07-pseudo-histories.md`. Promote when interest or a scenario needs them.
## Global pecking order

Today’s bipolar great powers sit on **classical West/East foundations** ([`10-classical-civilizations.md`](10-classical-civilizations.md)): Solara ← Helioran; Kharzhan State ← Shan-Khar.

### Tier 1 — Great powers (2)

| Power | Character |
| --- | --- |
| **Solara** | Maritime/tech hegemon on Solmar. Licenses, aerospace, navy, credit. |
| **Kharzhan State** | Continental industrial-military giant. Land power, magazines, clients (incl. Korvath). |

### Tier 2 — Major powers

| Power | Notes |
| --- | --- |
| **Veldara** (us) | Mini-US scale; Heartland grain federation + two coasts; modernizing from 80s–90s kit |
| **Korvath** | Other silo empire on the shared Eastmarch plain; pacing rival |
| **Nerath Compact** / **Tesen League** | Maravic belligerents |
| **Iberon Union** | Trade/workshop broker — not a peer fighter |

### Tier 3 — Regional (still on stage, thinner)

**Doverin** (partner catchment), **Sereth** (highland).

### Tier 4 — Footnotes

Everyone else.

## Wake-up call: the Maravic War

Farreach, Nerath vs Tesen, multi-year peer war, still grinding by default. Lessons: drones, AD, ammo surge, EW, legacy-force fragility.

## Arms market / nukes / our posture

Tiered market (Solara/Kharzhan strings on top systems). Nukes: great powers; we don't pursue in-series. Mandate after Maravic: full-domain generational jump ~15–20 years, interest-driven program order.
