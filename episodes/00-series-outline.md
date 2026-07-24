# Series Outline

> **Status:** living outline.
> This is design work — the reasoning behind each choice — presented in depth. Industry and cost are a **light supporting note**, not the subject.
> **Order is not fixed.** I tackle domains based on **what interests me and what I learn** as I go. The sequence below is a suggested default; reorder, skip ahead, or double back freely.

## Series in one sentence

A country with an 80s–90s military watches a modern war elsewhere, then executes a **full generational jump** across every domain — and I design the equipment on camera, explaining the trade-offs.

## Suggested default order (reorder freely)

A rough boring → exciting arc, but priorities follow my interest and learning:

1. Why jump — wake-up war, the legacy force, the budget (short)
2. Logistics
3. Soldier systems
4. C4ISR
5. Land
6. Air defense
7. Air force
8. Navy
9. Stress tests / revisiting earlier calls

Nothing here is a commitment. If drones or fighters are what I want to design next, that is where the series goes next.

## How deep each topic goes

Depth is driven by interest. A topic I care about can be several episodes; one I don't can be a single overview. The design doc holds the full reasoning; the episode(s) tell whichever parts are worth watching. A rough cost and build note per program is enough — don't let industry eat the runtime.

Typical beats for a program episode (use the ones that matter):

1. Requirement & legacy baseline
2. Options and trade-offs
3. Decision and why
4. Rough cost / build note (brief)
5. Fielding & knock-on effects

## Episode index (starter)

Treat IDs as stable; order as a reorderable default.

| ID | Working title | Source | Status |
| --- | --- | --- | --- |
| A0-01 | The Wake-Up Call | `world/00` | Not started |
| A0-02 | The 80s–90s Force We Actually Have | `world/01` | Not started |
| A0-03 | What the Jump Can Afford (rough) | `world/03`, `industry/README.md` | Not started |
| L-arc | Logistics | `designs/logistics/` | Not started |
| S-rifle | Rifle deep-dive | [`ep-soldier-rifle-arc.md`](ep-soldier-rifle-arc.md) | **Outlined (worked example)** |
| C-arc | C4ISR | `designs/c4isr/` | Not started |
| G-arc | Land combat | `designs/land/` | Not started |
| AD-arc | Air defense | `designs/air/` | Not started |
| AF-arc | Air force | `designs/air/` | Not started |
| N-arc | Navy | `designs/sea/` | Not started |
| Z-arc | Stress tests against scenarios | `threat-analysis/` | Not started |

## Standing rules

- Cold open on a design problem or a counterintuitive trade-off.
- Steelman rejected options.
- Numbers on screen come from `data/*.csv` (or are clearly labeled scenario fiction); rough is fine, just say so.
- Keep industry/cost brief — it supports the story, it isn't the story.
