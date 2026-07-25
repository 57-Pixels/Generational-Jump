# Maps quality ladder (Google-Maps-class zoom bands)

**Date:** 2026-07-25  
**Status:** approved (Build)  
**Constraint:** planet look first; canon seed / claim scoring deferred until morphology looks right.

## Goal

Make the viewer feel sharp at three zoom bands that work together:

| Band | Target | Tier / tiles |
| --- | --- | --- |
| Continent / country | Crisp coasts and ranges planet-wide | Global **`t1`** (~4.5 km) |
| Regional / campaign | Readable rivers, harbours, relief | Sparse deep tiles + **`t2`/`t3`** windows (~1 km → 250 m) |
| City / battlefield | ~100 m theater detail | Nested **`t4`** over Aurelian/Veldara |

Honest ceiling: ~100 m in-theater, not real Earth satellite / street imagery.

## Non-goals (this pass)

- Preserving seed 150 land fraction or claim scores
- Planet-wide 100 m (tile count and memory explode)
- New cartographic styles unrelated to resolution

## Architecture

1. **`--publish` raises morphology**, not just tile zoom: default tier **`t1`** (via existing T0→T1 upsample), equirect ≥4096×2048, global tiles z0–z6, deep tiles through z11 over theater windows.
2. **Nested refine is wired into generate/export**: extract Aurelian/Veldara windows, run `t2`→`t4` refine, composite refined elevation/color into deep tiles and in-window overlays.
3. **Viewer maxzoom tracks real detail** so MapLibre does not overzoom mush.
4. **Any seed is acceptable** for quality builds; re-promote canon later.

## Delivery slices

- **A:** `t1` publish path + viewer package regen + zoom caps  
- **B:** wire `refine.py` into pipeline, bake `t2`–`t4` into deep tiles  

## Success checks

- Published `world-meta.json` reports `tier=t1`, `face_n=2048` (or documented interim if memory forces staged `t0` first with explicit follow-up).
- Global coasts visibly sharper than prior `grid_n=64` package at the same camera.
- After slice B: deep-window tiles show sub-parent relief; downsampled refine still matches parent within existing refine RMS tests.
- `python3 -m unittest discover -s tests -p 'test_v2_*.py'` green.
