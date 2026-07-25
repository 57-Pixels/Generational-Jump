"""Declared field contract for v2 downstream consumers.

Enumerates every field name that ``model._deposit_context``, climate/hydrology
consumers, and export currently read. Adding a consumer of a new field requires
updating this module; removing a producer without updating it fails validation.
"""

from __future__ import annotations

from typing import Any

import numpy as np

GENERATOR_VERSION = "2.2.0"

# (dtype kind letter or 'dict', units, (lo, hi) or None for dicts/labels)
FieldSpec = tuple[str, str, tuple[float, float] | None]

GEOLOGY_SCALARS: dict[str, FieldSpec] = {
    "elevation_m": ("f", "m", (-12000.0, 9000.0)),
    "continental": ("f", "fraction", (0.0, 1.0)),
    "orogeny": ("f", "intensity", (0.0, 2.0)),
    "basin_depth": ("f", "fraction", (0.0, 1.0)),
    "sediment": ("f", "fraction", (0.0, 1.0)),
    "crust_thickness_km": ("f", "km", (5.0, 80.0)),
    "crust_age_ma": ("f", "Ma", (0.0, 4500.0)),
    "seafloor_age_ma": ("f", "Ma", (0.0, 250.0)),
}

GEOLOGY_HISTORY_KEYS: tuple[str, ...] = (
    "ridge",
    "continental_rift",
    "subduction",
    "arc",
    "collision",
    "suture",
    "transform",
    "passive_margin",
    "hydrothermal",
    "mafic",
    "alkaline",
    "exhumation",
)

GEOLOGY_LITHOLOGY_KEYS: tuple[str, ...] = (
    "ancient_craton",
    "felsic",
    "mafic",
    "ultramafic",
    "carbonate",
    "organic_shale",
    "sandstone",
    "evaporite",
    "quartz",
    "heavy_mineral_source",
)

GEOLOGY_PALEOCLIMATE_KEYS: tuple[str, ...] = (
    "wetland",
    "aridity",
    "tropical_weathering",
    "upwelling",
)

CLIMATE_FIELDS: dict[str, FieldSpec] = {
    "temperature_c": ("f", "C", (-90.0, 60.0)),
    "hottest_month_c": ("f", "C", (-80.0, 70.0)),
    "coldest_month_c": ("f", "C", (-100.0, 50.0)),
    "hottest_wet_bulb_c": ("f", "C", (-80.0, 50.0)),
    "precipitation_mm_yr": ("f", "mm/yr", (0.0, 10000.0)),
    "pet_mm_yr": ("f", "mm/yr", (0.0, 5000.0)),
    "humidity": ("f", "fraction", (0.0, 1.0)),
    "cdd24": ("f", "degree-days", (0.0, 20000.0)),
}

HYDROLOGY_FIELDS: dict[str, FieldSpec] = {
    "filled_elevation_m": ("f", "m", (-12000.0, 9000.0)),
    "depression_depth_m": ("f", "m", (0.0, 10000.0)),
    "drainage_area_km2": ("f", "km2", (0.0, 5.2e8)),
    "runoff_mm_yr": ("f", "mm/yr", (0.0, 10000.0)),
    "discharge_m3_s": ("f", "m3/s", (0.0, 1.0e8)),
    "delta_score": ("f", "fraction", (0.0, 1.0)),
    "river_mask": ("b", "bool", None),
    "lake_id": ("i", "label", None),
    "receiver": ("i", "index", None),
}

FIELD_CONTRACT: dict[str, Any] = {
    "geology_scalars": GEOLOGY_SCALARS,
    "geology_history": GEOLOGY_HISTORY_KEYS,
    "geology_lithology": GEOLOGY_LITHOLOGY_KEYS,
    "geology_paleoclimate": GEOLOGY_PALEOCLIMATE_KEYS,
    "climate": CLIMATE_FIELDS,
    "hydrology": HYDROLOGY_FIELDS,
}


class ContractError(ValueError):
    """Raised when a world fails the declared field contract."""


def _check_array(
    name: str,
    values: np.ndarray,
    kind: str,
    bounds: tuple[float, float] | None,
    errors: list[str],
) -> None:
    if not isinstance(values, np.ndarray):
        errors.append(f"{name}: expected ndarray, got {type(values).__name__}")
        return
    if kind == "f" and not np.issubdtype(values.dtype, np.floating):
        errors.append(f"{name}: expected floating dtype, got {values.dtype}")
    elif kind == "i" and not np.issubdtype(values.dtype, np.integer):
        errors.append(f"{name}: expected integer dtype, got {values.dtype}")
    elif kind == "b" and values.dtype != np.bool_ and not np.issubdtype(
        values.dtype, np.integer
    ):
        # bool masks may be bool_ or integer 0/1
        if values.dtype != np.bool_:
            errors.append(f"{name}: expected bool-like dtype, got {values.dtype}")
    if bounds is not None and np.issubdtype(values.dtype, np.number):
        finite = values[np.isfinite(values)]
        if finite.size:
            lo, hi = bounds
            vmin = float(finite.min())
            vmax = float(finite.max())
            if vmin < lo - 1e-6 or vmax > hi + 1e-6:
                errors.append(
                    f"{name}: values [{vmin:.4g}, {vmax:.4g}] outside [{lo}, {hi}]"
                )


def _check_dict_keys(
    label: str,
    mapping: dict[str, np.ndarray],
    required: tuple[str, ...],
    errors: list[str],
) -> None:
    missing = [key for key in required if key not in mapping]
    for key in missing:
        errors.append(f"{label}.{key}: missing")
    for key in required:
        if key not in mapping:
            continue
        _check_array(f"{label}.{key}", mapping[key], "f", (0.0, 1.5), errors)


def validate_contract(geology: Any, climate: Any, hydrology: Any) -> None:
    """Raise ``ContractError`` listing every missing or out-of-range field."""
    errors: list[str] = []

    for name, (kind, _units, bounds) in GEOLOGY_SCALARS.items():
        if not hasattr(geology, name):
            errors.append(f"geology.{name}: missing")
            continue
        _check_array(f"geology.{name}", getattr(geology, name), kind, bounds, errors)

    if not hasattr(geology, "history"):
        errors.append("geology.history: missing")
    else:
        _check_dict_keys(
            "geology.history", geology.history, GEOLOGY_HISTORY_KEYS, errors
        )

    if not hasattr(geology, "lithology"):
        errors.append("geology.lithology: missing")
    else:
        _check_dict_keys(
            "geology.lithology", geology.lithology, GEOLOGY_LITHOLOGY_KEYS, errors
        )

    if not hasattr(geology, "paleoclimate"):
        errors.append("geology.paleoclimate: missing")
    else:
        _check_dict_keys(
            "geology.paleoclimate",
            geology.paleoclimate,
            GEOLOGY_PALEOCLIMATE_KEYS,
            errors,
        )

    for name, (kind, _units, bounds) in CLIMATE_FIELDS.items():
        if not hasattr(climate, name):
            errors.append(f"climate.{name}: missing")
            continue
        _check_array(f"climate.{name}", getattr(climate, name), kind, bounds, errors)

    for name, (kind, _units, bounds) in HYDROLOGY_FIELDS.items():
        if not hasattr(hydrology, name):
            errors.append(f"hydrology.{name}: missing")
            continue
        _check_array(
            f"hydrology.{name}", getattr(hydrology, name), kind, bounds, errors
        )

    if errors:
        raise ContractError(
            "world failed field contract:\n  - " + "\n  - ".join(errors)
        )
