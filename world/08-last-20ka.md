# Last 20,000 Years — Human-Relevant Deep History

> **Scope:** civilization only needs **~20 ka → present**. Deeper tectonics stay in [`05-planetary-formation.md`](05-planetary-formation.md) as backdrop.
>
> **Method:** take **Earth’s conditions** in each period (ice, sea level, climate shocks) and apply them to *this* geography. Dates are Earth-analogue BP / BCE–CE; names are ours.
>
> **Timeline table:** [`09-historical-timeline.md`](09-historical-timeline.md)  
> **Maps:** generator supports `--era present` (default) and `--era lgm` ([`../maps/generator/`](../maps/generator/)).

## Ground rules

- Planet is an **Earth twin**: same orbital forcing, similar ice-sheet physics, similar melt rates.
- Humans are **native** (evolved here long before 20 ka). We do **not** narrate deep paleontology — only what matters once ice and coasts start moving hard.
- Country stories in [`07-pseudo-histories.md`](07-pseudo-histories.md) must not contradict this spine.

## Human hearth (working default)

> **[WORKING DEFAULT]** — overwrite if you prefer another cradle.

- **Hearth:** southern fringe of the **Kharzhan–Aurelian** northern world (warm coastal/river refugia through the LGM) — Earth “out of Africa” *role*, not Africa’s shape.
- By ~20 ka, people already live in patches on Aurelian, Kharzhan, and parts of Farreach; **Solmar** is reached via coastal/island hops along the West Ocean arc (harder, later dense settlement).

## What Earth teaches (apply 1:1 in spirit)

| Earth period (approx.) | Conditions we copy | Effect on *our* map |
| --- | --- | --- |
| **LGM ~26–19 ka BP** | Huge northern ice; sea level ≈ **−120 m**; cold, dry in many mid-lats; land bridges on shelves | Ice over northern Aurelian + northern Kharzhan; **East Gulf mostly dry plain/estuarine**; Westreach shelf wider; Solmar–arc hops easier; Heartland steppe-tundra mosaic |
| **Termination ~19–11.7 ka** | Pulsed melt, sea-level rise, meltwater pulses; unstable climates | Gulf floods stepwise; corridors open/close; megaflood scars on plains; human ranges shift |
| **Younger Dryas ~12.9–11.7 ka** | Sharp return toward glacial cold/dry in north | Northern abandonment pulses; Farreach tropics less hit; cultural “bottlenecks” |
| **Early Holocene ~11.7–8 ka** | Warming, sea level still rising toward modern; wetter phases in many places | Coasts approach modern; lakes fill Northwood; soils of future grain belts stabilize |
| **Holocene optimum / mid-Holocene** | Often warmer; monsoon/Hadley shifts; some desert expansions later | Farreach wet/dry flips; rain-shadow deserts pulse; agricultural windows open |
| **Late Holocene** | Near-modern seas; local droughts, floods, volcanism | Classic grain-barony geography locks in ([`06`](06-settlement-and-borders.md)) |
| **Last ~500 years** | Little Ice Age–analogue optional; industrial climate later | Early modern empires; Solara/Kharzhan rise; industrial coasts |

Exact °C and meters can stay “Earth-like”; the **direction of change** is what the sim and stories need.

## Map consequences we will actually use

### Last Glacial Maximum (generator `--era lgm`)

- Sea level lowered → **continental shelves exposed** (Westreach and East Gulf shelves especially).
- **East Gulf** is not today’s warm embayment — it is a low plain / braided river country (Mississippi-shelf *logic*).
- Northern **ice sheets** bury high-latitude Aurelian/Kharzhan; south of the ice, loess and outwash feed future Heartland fertility.
- **Land/ice corridors** matter more than modern passes; Highspine still blocks, but coastal plain west of it is wider.
- Solmar arc islands are less isolated (lower seas).

### Deglaciation

- Ice retreat dumps **lakes and disordered drainage** → Northwood.
- Sea rise **drowns** the East Gulf plain → today’s humid gulf + delta problem.
- Populations that lived on the shelf either move inland, take boats, or leave archaeological “drowned” stories (footnotes later).

### Holocene civilization window

- Stable enough coasts + glacial soils + rivers → **grain nodes** (the barony insight).
- Open **Eastmarch** plain never gets a glacial wall between future Veldara and Korvath → structural rivalry.
- Farreach suture stays a highland barrier; Maravic-scale conflict waits for modern logistics.
- By the classical era, two historically large packages dominate prestige memory: **Helioran (West)** and **Shan-Khar (East)** — [`10-classical-civilizations.md`](10-classical-civilizations.md). Everything after is partly their rematch.

## What we deliberately skip (for now)

- Pre-20 ka human evolution narrative
- Every Dansgaard–Oeschger wiggle by name
- Detailed isotope curves

Add detail only when an episode or sim tick needs it.

## Downstream

| Doc / tool | Uses this how |
| --- | --- |
| `09-historical-timeline.md` | Dated era list |
| `06` / `07` | Settlement & states sit in late Holocene+ |
| `maps/generator` | `--era lgm` vs `present` snapshots |
| Future `sim/` | Climate era flags change food yield and passability |
