# Fantasy Military Design Project

A worldbuilding and defense-design project set in a fictional world at **2025 technology, no magic**. I play the role of the defense designer for one country trying to ensure its survival. This repository is the single source of truth for a video series: every equipment decision traces back to documented world constraints, so each video can show *why* a choice was made, not just what it is.

## How the documents connect

```
world/  ──────►  threat-analysis/  ──────►  doctrine/  ──────►  designs/
(constraints)    (who wants us dead        (what survival        (what we buy
                  and how)                  requires)             or build, and why)
                                                                      │
                                                                      ▼
                                                                 episodes/
                                                                 (the videos)
```

Nothing in `designs/` is allowed to contradict `world/`. Nothing in `episodes/` is allowed to contradict `designs/`. When a canon decision is made anywhere, it gets a line in [`decisions-log.md`](decisions-log.md).

## Reading order

1. [`world/00-world-overview.md`](world/00-world-overview.md) — the world, the major powers, the tech baseline
2. [`world/01-our-nation.md`](world/01-our-nation.md) — our country: geography, people, economy, politics
3. [`world/02-neighbors-and-threats.md`](world/02-neighbors-and-threats.md) — who surrounds us
4. [`world/03-economy-and-industrial-base.md`](world/03-economy-and-industrial-base.md) — what we can afford and what we can build
5. [`world/04-alliances-and-diplomacy.md`](world/04-alliances-and-diplomacy.md) — who will (and won't) help us
6. [`threat-analysis/00-threat-overview.md`](threat-analysis/00-threat-overview.md) — ranked threats and the scenarios in `threat-analysis/scenarios/`
7. [`doctrine/00-national-defense-strategy.md`](doctrine/00-national-defense-strategy.md) — the strategy the equipment must serve
8. `designs/` — one design doc per equipment decision, organized by domain
9. [`episodes/00-series-outline.md`](episodes/00-series-outline.md) — how it all becomes videos

## Directory guide

| Path | Contents |
| --- | --- |
| `world/` | The world bible. Source of all constraints. |
| `threat-analysis/` | Ranked threat overview plus one scenario doc per plausible conflict. |
| `doctrine/` | National defense strategy and per-service doctrine as it emerges. |
| `designs/land/` | Armor, artillery, ground vehicles, air defense. |
| `designs/air/` | Fixed wing, rotary wing, drones. |
| `designs/sea/` | Surface, subsurface, coastal defense (if we have a coast at all). |
| `designs/c4isr/` | Command, control, communications, computers, intelligence, surveillance, reconnaissance. |
| `designs/soldier-systems/` | Rifles, optics, body armor, uniforms, individual kit. |
| `designs/logistics/` | Trucks, fuel, ammunition supply, maintenance, medical. |
| `episodes/` | Series outline and per-episode scripts. |
| `templates/` | Fixed templates for design docs, episode scripts, and threat scenarios. |
| `decisions-log.md` | Running log of canon decisions so canon stays consistent. |

## Workflow for a new equipment decision

1. Confirm the requirement traces to a scenario in `threat-analysis/scenarios/`.
2. Copy [`templates/design-doc.md`](templates/design-doc.md) into the right `designs/` subfolder.
3. Fill in every section — especially **Rejected alternatives**. That section is the video.
4. Record the final decision in [`decisions-log.md`](decisions-log.md).
5. Copy [`templates/episode-script.md`](templates/episode-script.md) into `episodes/` and draft the video.

## Status

Docs marked **[STARTER SUGGESTION]** are proposed defaults meant to be overwritten with real creative decisions. Docs marked **[WORKED EXAMPLE]** exist to demonstrate template depth and are fully replaceable.
