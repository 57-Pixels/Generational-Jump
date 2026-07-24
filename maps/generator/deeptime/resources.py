"""Geological resource prospects derived from deep-time fields.

Canon: world/13-resources-from-geology.md
Important strategic minerals must appear on the map as earned deposits — not plot paste.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

# id → (display name, RGB 0-1 for map markers)
RESOURCE_CATALOG: dict[str, tuple[str, tuple[float, float, float]]] = {
    "coal": ("Coal", (0.12, 0.12, 0.14)),
    "oil_gas": ("Oil & gas", (0.12, 0.45, 0.22)),
    "iron": ("Iron", (0.72, 0.28, 0.18)),
    "copper": ("Copper (porphyry)", (0.85, 0.48, 0.12)),
    "tin_tungsten": ("Tin / tungsten", (0.55, 0.35, 0.75)),
    "gold": ("Gold", (0.92, 0.78, 0.18)),
    "silver_base": ("Silver / base-metal", (0.75, 0.78, 0.82)),
    "rare_earths": ("Rare earths", (0.85, 0.25, 0.65)),
    "uranium": ("Uranium", (0.45, 0.85, 0.25)),
    "silica_hp": ("High-purity silica", (0.85, 0.92, 0.95)),
    "bauxite": ("Bauxite (aluminum)", (0.78, 0.55, 0.28)),
    "nickel_pgm": ("Nickel / PGM", (0.35, 0.55, 0.70)),
    "lithium": ("Lithium (brine/pegmatite)", (0.55, 0.75, 0.90)),
    "phosphates": ("Phosphates", (0.40, 0.65, 0.35)),
    "potash": ("Potash", (0.65, 0.40, 0.55)),
}

# Cap markers so the atlas stays readable; all types still get representation.
MAX_PER_TYPE = 14
MIN_PER_TYPE = 3


@dataclass
class ResourceBundle:
    """Prospect intensity rasters + discrete deposit features."""

    intensity: dict[str, np.ndarray]  # 0..1 per resource id
    deposits: list[dict]  # GeoJSON-ready feature props + lon/lat
    overlay_rgb: np.ndarray  # float RGB atlas with markers
    legend: list[dict]


def _local_maxima(field: np.ndarray, mask: np.ndarray, min_dist: int) -> list[tuple[int, int, float]]:
    """Greedy peaks on masked field."""
    h, w = field.shape
    work = np.where(mask, field, -1.0).copy()
    peaks: list[tuple[int, int, float]] = []
    while True:
        idx = int(np.argmax(work))
        y, x = divmod(idx, w)
        val = float(work[y, x])
        if val <= 0.08:
            break
        peaks.append((y, x, val))
        y0, y1 = max(0, y - min_dist), min(h, y + min_dist + 1)
        x0, x1 = max(0, x - min_dist), min(w, x + min_dist + 1)
        work[y0:y1, x0:x1] = -1.0
        if len(peaks) >= MAX_PER_TYPE * 2:
            break
    return peaks


def compute_resource_fields(
    elev: np.ndarray,
    sea: float,
    cont: np.ndarray,
    orogeny: np.ndarray,
    ocean_age: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    moisture: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Prospect *intensity* 0..1 from geologic proxies (world/13)."""
    land = elev >= sea
    abs_lat = np.abs(lat)
    # Margins
    cont_e = np.roll(cont, -1, axis=1)
    cont_w = np.roll(cont, 1, axis=1)
    passive_margin = land & (cont > 0.35) & ((cont_e < 0.25) | (cont_w < 0.25)) & (orogeny < 0.25)
    arc_belt = land & (orogeny > 0.35) & (cont > 0.25)
    suture = land & (orogeny > 0.55) & (cont > 0.4)
    craton_core = land & (cont > 0.7) & (orogeny < 0.18) & (abs_lat < 60)
    interior_basin = land & (cont > 0.45) & (orogeny < 0.22) & (elev < sea + 0.35)
    shelf = (~land) & (elev > sea - 0.35) & (ocean_age > 0.2)
    foreland = land & (orogeny > 0.15) & (orogeny < 0.45) & (cont > 0.4)
    wet_tropics = land & (moisture > 0.55) & (abs_lat < 25)
    arid_basin = land & (moisture < 0.35) & interior_basin
    coastal_sand = land & passive_margin & (abs_lat < 45)
    # Noise so deposits aren't perfect geometric rings
    n1 = rng.random(elev.shape)
    n2 = rng.random(elev.shape)

    fields: dict[str, np.ndarray] = {}

    fields["coal"] = (
        interior_basin.astype(np.float64) * 0.55
        + foreland.astype(np.float64) * 0.35
        + (moisture > 0.4).astype(np.float64) * 0.15
    ) * (0.7 + 0.3 * n1)

    fields["oil_gas"] = (
        shelf.astype(np.float64) * 0.55
        + passive_margin.astype(np.float64) * 0.45
        + foreland.astype(np.float64) * 0.25
        + (elev < sea).astype(np.float64) * shelf.astype(np.float64) * 0.2
    ) * (0.65 + 0.35 * n2)

    fields["iron"] = (
        craton_core.astype(np.float64) * 0.65
        + (craton_core & (n1 > 0.55)).astype(np.float64) * 0.25
        + arc_belt.astype(np.float64) * 0.15
    )

    fields["copper"] = arc_belt.astype(np.float64) * (0.5 + 0.5 * np.clip(orogeny, 0, 1)) * (
        0.6 + 0.4 * n1
    )

    fields["tin_tungsten"] = (
        suture.astype(np.float64) * 0.55 + arc_belt.astype(np.float64) * 0.25
    ) * (0.6 + 0.4 * n2)

    # Gold: hydrothermal arc/suture + placer-ish lowland downstream proxy (near arc, lower elev)
    fields["gold"] = (
        arc_belt.astype(np.float64) * 0.45
        + suture.astype(np.float64) * 0.35
        + (land & (orogeny > 0.2) & (elev < sea + 0.45)).astype(np.float64) * 0.25
    ) * (0.55 + 0.45 * n1)

    fields["silver_base"] = (
        arc_belt.astype(np.float64) * 0.4 + suture.astype(np.float64) * 0.3
    ) * (0.5 + 0.5 * n2)

    # REE: alkaline/craton intrusions + heavy-mineral sands
    fields["rare_earths"] = (
        (craton_core & (n2 > 0.62)).astype(np.float64) * 0.7
        + coastal_sand.astype(np.float64) * 0.45
        + (suture & (n1 > 0.7)).astype(np.float64) * 0.25
    )

    fields["uranium"] = (
        interior_basin.astype(np.float64) * 0.45
        + (craton_core & (n1 > 0.75)).astype(np.float64) * 0.4
        + foreland.astype(np.float64) * 0.2
    ) * (0.6 + 0.4 * n2)

    # High-purity silica: clean quartz sands (passive coasts) + high-grade quartzite in old craton
    fields["silica_hp"] = (
        coastal_sand.astype(np.float64) * 0.55
        + (craton_core & (orogeny < 0.12) & (n2 > 0.5)).astype(np.float64) * 0.5
        + (passive_margin & (moisture < 0.5)).astype(np.float64) * 0.25
    )

    fields["bauxite"] = wet_tropics.astype(np.float64) * (0.5 + 0.4 * n1) * (
        cont > 0.35
    ).astype(np.float64)

    # Nickel / PGM: mafic–ultramafic / greenstone analogue on craton margins + some suture
    craton_edge = land & (cont > 0.45) & (cont < 0.75) & (orogeny < 0.3)
    fields["nickel_pgm"] = (
        craton_edge.astype(np.float64) * 0.55 + suture.astype(np.float64) * 0.25
    ) * (0.55 + 0.45 * n2)

    fields["lithium"] = (
        arid_basin.astype(np.float64) * 0.55
        + (suture & (n1 > 0.65)).astype(np.float64) * 0.4  # pegmatite belts
    )

    fields["phosphates"] = (
        shelf.astype(np.float64) * 0.4
        + (passive_margin & (abs_lat < 40)).astype(np.float64) * 0.45
        + (interior_basin & (n2 > 0.6)).astype(np.float64) * 0.25
    )

    fields["potash"] = (
        (interior_basin & (moisture < 0.45)).astype(np.float64) * 0.6
        + arid_basin.astype(np.float64) * 0.35
    )

    # Normalize; oil/phosphates may sit on shelf; most ores are land-bound
    out: dict[str, np.ndarray] = {}
    for rid, f in fields.items():
        f = np.clip(f, 0, None)
        if rid in ("oil_gas", "phosphates"):
            f = np.where(land | shelf, f, 0.0)
        else:
            f = np.where(land, f, 0.0)
        mx = float(f.max()) if f.size else 0.0
        out[rid] = f / mx if mx > 1e-6 else f
    return out


def pick_deposits(
    fields: dict[str, np.ndarray],
    lon: np.ndarray,
    lat: np.ndarray,
    elev: np.ndarray,
    sea: float,
    rng: np.random.Generator,
) -> list[dict]:
    h, w = next(iter(fields.values())).shape
    min_dist = max(6, min(h, w) // 40)
    deposits: list[dict] = []
    dep_id = 0
    for rid, field in fields.items():
        name, _ = RESOURCE_CATALOG[rid]
        # Allow oil on shelf (elev slightly below sea)
        if rid == "oil_gas":
            mask = field > 0.12
        else:
            mask = (elev >= sea - 0.05) & (field > 0.12)
        peaks = _local_maxima(field, mask, min_dist=min_dist)
        # Keep top by value, ensure minimum if possible
        peaks = sorted(peaks, key=lambda p: p[2], reverse=True)
        keep = peaks[:MAX_PER_TYPE]
        if len(keep) < MIN_PER_TYPE and len(peaks) > len(keep):
            keep = peaks[:MIN_PER_TYPE]
        # If still starved, force random samples from high quantile
        if len(keep) < MIN_PER_TYPE:
            ys, xs = np.where(field >= np.quantile(field, 0.92))
            if len(ys):
                pick_n = min(MIN_PER_TYPE - len(keep), len(ys))
                sel = rng.choice(len(ys), size=pick_n, replace=False)
                for i in sel:
                    keep.append((int(ys[i]), int(xs[i]), float(field[ys[i], xs[i]])))
        for y, x, val in keep:
            grade = "major" if val > 0.65 else "significant" if val > 0.4 else "minor"
            deposits.append(
                {
                    "id": f"{rid}-{dep_id}",
                    "resource": rid,
                    "name": name,
                    "grade": grade,
                    "intensity": round(val, 3),
                    "lon": float(lon[y, x]),
                    "lat": float(lat[y, x]),
                }
            )
            dep_id += 1
    return deposits


def render_resource_overlay(
    base_rgb: np.ndarray, deposits: list[dict]
) -> np.ndarray:
    """Draw deposit markers on a copy of the atlas color image."""
    h, w, _ = base_rgb.shape
    img = Image.fromarray((np.clip(base_rgb, 0, 1) * 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(img)
    r = max(2, min(h, w) // 180)
    for d in deposits:
        # pixel from lon/lat
        x = int((d["lon"] + 180.0) / 360.0 * w) % w
        y = int((90.0 - d["lat"]) / 180.0 * h)
        y = int(np.clip(y, 0, h - 1))
        _, rgb = RESOURCE_CATALOG[d["resource"]]
        color = tuple(int(c * 255) for c in rgb)
        # major = filled square-ish; others = circle
        if d["grade"] == "major":
            draw.rectangle([x - r, y - r, x + r, y + r], fill=color, outline=(20, 20, 20))
        else:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=(20, 20, 20))
    return np.asarray(img).astype(np.float64) / 255.0


def deposits_geojson(deposits: list[dict]) -> dict:
    return {
        "type": "FeatureCollection",
        "name": "geological-resources",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": d["id"],
                    "resource": d["resource"],
                    "name": d["name"],
                    "grade": d["grade"],
                    "intensity": d["intensity"],
                },
                "geometry": {"type": "Point", "coordinates": [d["lon"], d["lat"]]},
            }
            for d in deposits
        ],
    }


def build_resources(
    elev: np.ndarray,
    sea: float,
    cont: np.ndarray,
    orogeny: np.ndarray,
    ocean_age: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    moisture: np.ndarray,
    base_color: np.ndarray,
    seed: int,
) -> ResourceBundle:
    rng = np.random.default_rng(seed + 7919)
    fields = compute_resource_fields(
        elev, sea, cont, orogeny, ocean_age, lat, lon, moisture, rng
    )
    deposits = pick_deposits(fields, lon, lat, elev, sea, rng)
    overlay = render_resource_overlay(base_color, deposits)
    legend = [
        {"id": rid, "name": name, "color_rgb": [round(c, 3) for c in rgb]}
        for rid, (name, rgb) in RESOURCE_CATALOG.items()
    ]
    # counts
    counts: dict[str, int] = {rid: 0 for rid in RESOURCE_CATALOG}
    for d in deposits:
        counts[d["resource"]] = counts.get(d["resource"], 0) + 1
    for item in legend:
        item["deposit_count"] = counts.get(item["id"], 0)
    return ResourceBundle(
        intensity=fields, deposits=deposits, overlay_rgb=overlay, legend=legend
    )
