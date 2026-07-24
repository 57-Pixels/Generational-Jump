# Decisions Log

Running log of canon decisions. Binding until superseded. Newest at the bottom; IDs never reused. Starter suggestions in prose are **not** canon until they have a row here.

| ID | Date | Decision | Where it lives | Supersedes |
| --- | --- | --- | --- | --- |
| D-0000 | 2026-07-24 | Ground rules: real-world 2025 tech, no magic, fictional geography, real physics/economics | `world/00-world-overview.md` | — |
| D-0001 | 2026-07-24 | **[WORKED EXAMPLE]** Infantry rifle `rifle-std-1`: license-build a modern design on the retooled domestic plant; surplus only as a time-boxed training bridge; single caliber. Rough cost in `data/costs.csv` | `designs/soldier-systems/infantry-rifle.md`, `data/*` | — |
| D-0002 | 2026-07-24 | Series premise: distant-war wake-up; start from 80s–90s force; full-domain generational jump. Focus is design reasoning | `README.md`, `world/00`, `doctrine/00`, `episodes/00` | — |
| D-0003 | 2026-07-24 | Series order and depth are **interest-driven**, not fixed. The boring→exciting sequence in `episodes/00` is a reorderable default | `episodes/00-series-outline.md`, `doctrine/00` | — |
| D-0004 | 2026-07-24 | Costing currency is project-dollars (`PD`); numbers are rough estimates (tagged `rough`/`study`/`firm`) in `data/costs.csv`; CSV column names stay stable for a future site | `industry/README.md`, `data/README.md` | — |
| D-0005 | 2026-07-24 | **Industry is a light supporting note, not the focus** — often AI-assisted. Removed per-station production-line data, multi-year cost ramps, detailed BOM, and the manufacturing-appendix template; kept one short industry section per design doc plus simple `programs.csv`/`costs.csv` | `industry/README.md`, `templates/design-doc.md`, `data/` | Simplifies D-0002/D-0004 industrial scope |
| D-0006 | 2026-07-24 | **World pecking order:** Tier1 great powers Solara (maritime/tech) + Kharzhan State (continental); Tier2 majors include Veldara (us), Korvath, Nerath Compact, Tesen League, Iberon Union; wake-up war = Maravic War on Farreach | `world/00-world-overview.md` | — |
| D-0007 | 2026-07-24 | **Veldara = mini-US-scale major power:** ~3.2M km², ~110M people, ~$5.5T GDP, two coasts (West Ocean + East Gulf), federal republic; regions Westreach/Highspine/Heartland/Northwood/Eastmarch/Gulf Coast/Southmere | `world/01-our-nation.md`, `maps/01-country-maps-brief.md` | Replaces older small-country starters |
| D-0008 | 2026-07-24 | Map pipeline: world image-gen brief → upscale ~16k → label; then multi-type Veldara map set. Locked master coastlines override prose | `maps/00-world-map-brief.md`, `maps/01-country-maps-brief.md` | — |
