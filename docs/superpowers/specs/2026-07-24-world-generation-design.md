# World Generation Design — Deep Time → Culture → Jump

**Date:** 2026-07-24  
**Status:** approved to build (user: "Lets build this thing now")  
**Repo:** Generational-Jump

## Purpose

Generate believable fictional worlds for military-design stories where **2025 tech** is earned by an Earthlike **sequence of events**, not pasted on. Each new story *may* run a fresh deep-time seed; comprehension and path-dependence still require Earth-analogue *roles*.

## Core principles

1. **Continent = continental plate.** A **landmass** is continuous dry land and may contain multiple continents (e.g. collided Nerath + Tesen = Farreach landmass).
2. **~Earth land fraction** at present (~29% land / ~71% ocean). LGM raises land via lower seas.
3. **Environment → culture.** Classical packages and modern traits must be causable by local food, transport, climate, and barriers.
4. **Humans build on forefathers.** Languages, law, doctrine, and industry inherit from earlier layers (classical → vernacular → industrial → legacy force → generational jump).
5. **Path dependence.** Industrial modernity needs the event-*types* of Earth’s stack (surplus agriculture → classical states/literacy/law → early modern science/trade → fossil industry → industrial war). Roles, not Earth names.
6. **Earth mirroring is for comprehension + causality**, not cosplay. Prefer familiar patterns when they help; break when the map earns it; never use Earth proper names on the map.
7. **Detail scales with recency.** Deep time coarse; classical enough for inheritance; last century / Maravic / jump fully detailed.
8. **History depth by relevance:** important/neighbors · odd-ones-out (improbable states) · countries of interest. Footnotes otherwise.
9. **Classical isolation:** West/East giants barely meet until early modern because of **oceans + mountains + deserts** (Rome/China *logic*).

## Pipeline

```
seed
  → deep-time plate sim (Ga → present)
  → heightfield + plate map (~29% land)
  → climate / moisture
  → settlement & food cores (coarse)
  → classical hearths earned by environment
  → language/culture stems + legends (roles)
  → on-stage modern states (neighbors, patrons, odd ones, interest)
  → legacy forces → Maravic wake-up → generational jump series
```

Unique story = new seed (optional) producing a new board **and** a new ancestral stack that still obeys the sequence.

## Deep-time sim (v1 scope)

**Goal:** Level-3 *spirit* — plates evolve over deep time so continents form by rift / subduction / collision, not ellipse paste.

**v1 method (ship now):**
- Equirectangular grid; continental vs oceanic crust; plate IDs + velocities
- Tick in Ma steps: advect, grow ridges, consume trenches, raise sutures/arcs, age ocean crust
- Accumulate orogeny; derive elevation; set sea level so land ≈ 29%
- Soft **hooks** (reject/reroll or warn): wide inter-hearth ocean, ≥1 suture landmass, ≥1 subduction cordillera with passive opposite coast, arid/mountain barriers possible

**Not in v1:** full mantle CFD, paleoclimate GCM, automatic nation naming.

**Reference campaign:** frozen Generational-Jump / Veldara geography remains a named seed artifact until regenerated deliberately.

## Story hooks (filters)

| Hook | Why |
| --- | --- |
| Land fraction ~0.29 ± tolerance | Familiar logistics |
| ≥1 wide ocean between major continental plates | Classical non-meeting |
| ≥1 continent–continent suture landmass | Maravic-type theater |
| ≥1 subduction margin + opposing passive margin | Asymmetric major-power board |
| Two distant classical-capable hearths | Helioran / Shan-Khar *roles* |

## Cultural layer (after map)

| Environment | Cultural pressure | Classical role |
| --- | --- | --- |
| Maritime littoral / islands | Shipping as highway | Helioran-type (law, navy) |
| Irrigated river plains | Flood + grain boards | Shan-Khar-type (exams, census) |
| Open grain plains | Contested surplus | Breadbasket frontier |
| Suture + arid flanks | Hard war geography | Farreach-type |

Legendary figures are **roles** (Alexander-scale, lawgiver, canal-tamer) with *this* world’s names — see `world/11-legendary-figures.md`.

## Fidelity by time and polity

| When | Detail |
| --- | --- |
| Deep time | Process + seed parameters |
| Classical | Stems, barriers, S/A-tier legends |
| Early modern → industrial | Power geography, trade, force habits |
| ~last 100y → now | Full: TOE, programs, doctrine |

| Who gets history | Depth |
| --- | --- |
| Important / neighbors | Full stack |
| Odd ones out | Enough to explain survival |
| Countries of interest | As needed by scenario |
| Everyone else | Footnote |

## Repo layout

| Path | Role |
| --- | --- |
| `maps/generator/deeptime/` | Deep-time sim + CLI |
| `maps/generator/generate_world.py` | Legacy ellipse generator (reference); deeptime becomes default path |
| `world/05-planetary-formation.md` | Physics + definitions; campaign-specific shapes = seed artifacts |
| `world/12-worldbuilding-principles.md` | Principles above (short bible page) |
| `decisions-log.md` | D-0017+ |

## Success criteria (v1)

- [ ] `python3 -m deeptime` (or CLI) produces height + color PNG from `--seed`
- [ ] Present land fraction within ~0.26–0.32
- [ ] Different seeds → visibly different continents
- [ ] Meta JSON records seed, ticks, land fraction, hook results
- [ ] Principles + plate definition logged in decisions-log
- [ ] Viewer can load deeptime export (same filenames or documented path)
