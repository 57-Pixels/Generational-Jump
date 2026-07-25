"""Resolution ladder for nested morphology."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    name: str
    grid_n: int | None
    target_km: float | None
    windowed: bool


TIERS: tuple[Tier, ...] = (
    Tier("t0", 256, 35.0, False),
    Tier("t1", 2048, 4.5, False),
    Tier("t2", None, 1.0, True),
    Tier("t3", None, 0.25, True),
    Tier("t4", None, 0.1, True),
    # Dev/default: honour WorldConfig.grid_n (keeps existing tests fast).
    Tier("dev", None, None, False),
)

_TIER_BY_NAME = {tier.name: tier for tier in TIERS}


def get_tier(name: str) -> Tier:
    try:
        return _TIER_BY_NAME[name]
    except KeyError as exc:
        known = ", ".join(sorted(_TIER_BY_NAME))
        raise ValueError(f"unknown tier {name!r}; expected one of: {known}") from exc


def resolve_grid_n(tier_name: str, grid_n: int) -> int:
    """Return the face resolution for a tier.

    Windowed and ``dev`` tiers keep the caller-supplied ``grid_n``.
    """
    tier = get_tier(tier_name)
    if tier.grid_n is None:
        return grid_n
    return int(tier.grid_n)
