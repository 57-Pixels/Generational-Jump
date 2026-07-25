"""Resolve CLI export settings for quality publish packages."""

from __future__ import annotations

from dataclasses import dataclass

from .v2.tiers import resolve_grid_n
from .v2.tiles import DEFAULT_DEEP_MAX_ZOOM, DEFAULT_GLOBAL_MAX_ZOOM


@dataclass(frozen=True)
class PublishSettings:
    tier: str
    grid_n: int
    export_width: int
    export_height: int
    tile_global_max_zoom: int
    tile_deep_max_zoom: int


def resolve_publish_settings(
    *,
    tier: str,
    grid_n: int,
    width: int,
    height: int,
    publish: bool,
    tile_global_max_zoom: int | None = None,
    tile_deep_max_zoom: int | None = None,
) -> PublishSettings:
    """Map CLI flags to morphology + tile export settings.

    ``--publish`` raises the default morphology to ``t1`` and ships the full
    sparse pyramid (global z0–z6, deep through z11) with a dense equirect.
    An explicit ``--tier t0|t1|...`` still wins for morphology.
    """
    out_tier = tier
    if publish and tier == "dev":
        out_tier = "t1"
    out_grid_n = resolve_grid_n(out_tier, grid_n)

    if publish:
        tile_global = DEFAULT_GLOBAL_MAX_ZOOM
        tile_deep = DEFAULT_DEEP_MAX_ZOOM
        export_width = max(width, 4096)
        export_height = max(height, 2048)
    elif out_tier in ("t0", "t1"):
        tile_global = DEFAULT_GLOBAL_MAX_ZOOM
        tile_deep = DEFAULT_DEEP_MAX_ZOOM
        export_width = width
        export_height = height
    else:
        tile_global = 2
        tile_deep = 3
        export_width = width
        export_height = height

    if tile_global_max_zoom is not None:
        tile_global = tile_global_max_zoom
    if tile_deep_max_zoom is not None:
        tile_deep = tile_deep_max_zoom

    return PublishSettings(
        tier=out_tier,
        grid_n=out_grid_n,
        export_width=export_width,
        export_height=export_height,
        tile_global_max_zoom=tile_global,
        tile_deep_max_zoom=tile_deep,
    )
