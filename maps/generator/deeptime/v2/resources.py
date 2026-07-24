"""History-derived strategic deposits and bulk geological materials."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DepositSpec:
    id: str
    display_name: str
    factors: tuple[str, ...]
    rate_per_million_km2: float
    median_tonnage: float
    grade_key: str
    median_grade: float
    offshore: bool = False
    processing_base: float = 0.4
    byproducts: tuple[str, ...] = ()


DEPOSIT_CATALOG = (
    DepositSpec("coal_basin", "Coal basin", ("wetland", "basin", "organic_shale", "maturity"), 0.10, 2e9, "coal_quality", 0.65, processing_base=0.25, byproducts=("germanium", "coalbed_methane")),
    DepositSpec("petroleum_system", "Oil & gas", ("source", "maturity", "reservoir", "seal", "trap"), 0.10, 8e8, "boe_per_t", 0.12, offshore=True, processing_base=0.45, byproducts=("helium", "sulfur")),
    DepositSpec("helium_gas", "Helium-bearing gas", ("stable", "reservoir", "seal", "trap", "felsic"), 0.035, 8e7, "helium_vol_pct", 0.6, processing_base=0.75, byproducts=("natural_gas",)),
    DepositSpec("bif_iron", "Banded iron", ("ancient_craton", "stable", "exhumation"), 0.075, 1.5e9, "fe_pct", 48.0, processing_base=0.35),
    DepositSpec("bauxite_laterite", "Bauxite", ("weathering", "stable", "felsic"), 0.065, 3e8, "al2o3_pct", 46.0, processing_base=0.5, byproducts=("gallium", "scandium")),
    DepositSpec("sedimentary_manganese", "Manganese", ("shelf", "redox", "upwelling"), 0.055, 1.5e8, "mn_pct", 28.0, offshore=True, processing_base=0.5, byproducts=("cobalt", "nickel")),
    DepositSpec("vanadium_titanomagnetite", "Titanium–vanadium magnetite", ("mafic", "stable"), 0.05, 5e8, "tio2_pct", 18.0, processing_base=0.7, byproducts=("iron", "vanadium", "scandium")),
    DepositSpec("layered_chromite_pgm", "Chromium / PGM", ("mafic", "ultramafic", "stable"), 0.045, 1.2e8, "cr2o3_pct", 31.0, processing_base=0.7, byproducts=("platinum_group", "nickel", "cobalt", "gold")),
    DepositSpec("porphyry_cu_mo", "Porphyry copper", ("arc", "hydrothermal", "felsic", "exhumation"), 0.10, 1e9, "cu_pct", 0.55, processing_base=0.55, byproducts=("molybdenum", "rhenium", "gold", "silver", "tellurium")),
    DepositSpec("sediment_cu_co", "Sediment-hosted copper–cobalt", ("rift", "brine", "redox", "sediment"), 0.055, 2e8, "cu_pct", 2.0, processing_base=0.5, byproducts=("cobalt", "silver", "germanium")),
    DepositSpec("vms_cu_zn", "Volcanogenic Cu–Zn", ("rift_or_arc", "hydrothermal", "mafic"), 0.065, 5e7, "combined_base_pct", 7.0, processing_base=0.72, byproducts=("gold", "silver", "indium", "germanium")),
    DepositSpec("sedex_zn_pb", "Sedimentary Zn–Pb", ("rift", "basin", "restricted", "brine"), 0.05, 1.8e8, "zn_pb_pct", 8.0, processing_base=0.65, byproducts=("silver", "germanium", "cadmium")),
    DepositSpec("mvt_zn_pb", "Carbonate Zn–Pb", ("carbonate", "brine", "trap"), 0.05, 1.2e8, "zn_pb_pct", 7.0, processing_base=0.55, byproducts=("germanium", "gallium", "cadmium")),
    DepositSpec("magmatic_ni_cu", "Magmatic nickel–copper", ("mafic", "ultramafic", "hydrothermal"), 0.055, 1.2e8, "ni_pct", 1.1, processing_base=0.62, byproducts=("copper", "cobalt", "platinum_group")),
    DepositSpec("nickel_laterite", "Nickel laterite", ("ultramafic", "weathering", "stable"), 0.055, 3e8, "ni_pct", 1.35, processing_base=0.82, byproducts=("cobalt", "scandium")),
    DepositSpec("granite_sn_w", "Tin / tungsten granite", ("collision", "felsic", "hydrothermal", "exhumation"), 0.055, 6e7, "sn_w_pct", 0.55, processing_base=0.7, byproducts=("molybdenum", "bismuth", "lithium")),
    DepositSpec("hydrothermal_gold", "Gold", ("collision_or_arc", "hydrothermal", "exhumation"), 0.11, 4e7, "au_g_t", 3.0, processing_base=0.65, byproducts=("silver", "copper", "tellurium", "antimony")),
    DepositSpec("antimony_hydrothermal", "Antimony", ("collision", "hydrothermal", "sediment"), 0.035, 8e6, "sb_pct", 4.0, processing_base=0.7, byproducts=("gold", "silver")),
    DepositSpec("uranium_system", "Uranium", ("stable", "redox", "sandstone", "felsic"), 0.055, 2e7, "u3o8_pct", 0.18, processing_base=0.62, byproducts=("vanadium", "molybdenum", "rare_earths")),
    DepositSpec("carbonatite_ree_nb", "Rare earths / niobium", ("alkaline", "stable", "carbonate"), 0.045, 1.8e8, "treo_pct", 2.2, processing_base=0.88, byproducts=("niobium", "phosphate", "tantalum", "uranium", "thorium")),
    DepositSpec("ionic_clay_hree", "Heavy rare-earth clay", ("felsic", "weathering", "stable"), 0.035, 8e7, "treo_pct", 0.12, processing_base=0.9, byproducts=("heavy_rare_earths",)),
    DepositSpec("mineral_sands", "Titanium / zircon mineral sands", ("heavy_mineral", "coastal_reworking", "shelf"), 0.07, 2e8, "heavy_mineral_pct", 6.0, offshore=True, processing_base=0.5, byproducts=("titanium", "zirconium", "hafnium", "rare_earths")),
    DepositSpec("lithium_brine", "Lithium brine", ("closed", "aridity", "basin", "felsic"), 0.045, 4e7, "li_mg_l", 650.0, processing_base=0.7, byproducts=("potassium", "boron")),
    DepositSpec("lct_pegmatite", "Lithium pegmatite", ("collision", "felsic", "exhumation"), 0.055, 5e7, "li2o_pct", 1.3, processing_base=0.58, byproducts=("tantalum", "cesium", "beryllium", "tin")),
    DepositSpec("metamorphic_graphite", "Natural graphite", ("organic_shale", "collision", "exhumation"), 0.055, 7e7, "tgc_pct", 12.0, processing_base=0.72),
    DepositSpec("phosphorite", "Phosphate", ("shelf", "upwelling", "redox"), 0.075, 6e8, "p2o5_pct", 24.0, offshore=True, processing_base=0.45, byproducts=("uranium", "rare_earths", "fluorine")),
    DepositSpec("potash_evaporite", "Potash", ("restricted", "basin", "evaporite", "aridity"), 0.055, 8e8, "k2o_pct", 22.0, processing_base=0.45, byproducts=("magnesium_salts",)),
    DepositSpec("fluorspar_hydrothermal", "Fluorspar", ("rift_or_alkaline", "hydrothermal", "carbonate"), 0.045, 4e7, "caf2_pct", 55.0, processing_base=0.58, byproducts=("barite", "lead", "zinc", "rare_earths")),
    DepositSpec("high_purity_quartz", "High-purity quartz", ("quartz", "hydrothermal", "exhumation", "purity"), 0.018, 2e6, "impurity_ppm", 35.0, processing_base=0.92),
)


@dataclass
class DepositContext:
    area_km2: np.ndarray
    land: np.ndarray
    lon_deg: np.ndarray
    lat_deg: np.ndarray
    slope: np.ndarray
    ruggedness: np.ndarray
    water_depth: np.ndarray
    water_stress: np.ndarray
    factors: dict[str, np.ndarray]

    @property
    def size(self) -> int:
        return len(self.area_km2)

    @classmethod
    def zeros(cls, size: int) -> "DepositContext":
        zero = np.zeros(size)
        return cls(
            area_km2=np.full(size, 100_000.0),
            land=np.ones(size, dtype=bool),
            lon_deg=np.linspace(-180, 180, size, endpoint=False),
            lat_deg=np.zeros(size),
            slope=zero.copy(),
            ruggedness=zero.copy(),
            water_depth=zero.copy(),
            water_stress=zero.copy(),
            factors={},
        )

    @classmethod
    def synthetic_hosted(cls, size: int) -> "DepositContext":
        result = cls.zeros(size)
        keys = {factor for spec in DEPOSIT_CATALOG for factor in spec.factors}
        result.factors = {key: np.full(size, 0.82) for key in keys}
        return result


@dataclass
class Deposit:
    id: str
    deposit_class: str
    name: str
    lon: float
    lat: float
    prospect_score: float
    ore_resource_t: float
    grade: dict[str, float]
    depth_m: float
    accessibility: float
    processing_difficulty: float
    recovery: float
    reserve_2025_t: float
    byproducts: tuple[str, ...]


def _geologic_and(arrays: list[np.ndarray]) -> np.ndarray:
    if not arrays:
        raise ValueError("at least one factor is required")
    values = np.stack([np.clip(array, 0.0, 1.0) for array in arrays])
    # One weak proxy lowers suitability without making every real multi-stage
    # system mathematically impossible. A completely absent host remains zero.
    zero = np.all(values <= 0.0, axis=0)
    result = np.exp(np.mean(np.log(np.maximum(values, 0.02)), axis=0))
    result[zero] = 0.0
    return result


def _bulk_materials(context: DepositContext) -> dict[str, np.ndarray]:
    f = context.factors
    size = context.size
    get = lambda name: np.clip(f.get(name, np.zeros(size)), 0, 1)
    access = (1.0 - context.slope) * (1.0 - 0.6 * context.ruggedness)
    return {
        "aggregate": np.clip(access * (0.4 + 0.6 * get("stable")), 0, 1),
        "sand_gravel": np.clip(access * (0.5 * get("sediment") + 0.5 * get("coastal_reworking")), 0, 1),
        "limestone": np.clip(access * get("carbonate"), 0, 1),
        "brick_clay": np.clip(access * get("sediment"), 0, 1),
        "common_silica_sand": np.clip(access * get("quartz") * get("sediment"), 0, 1),
        "gypsum": np.clip(access * get("evaporite"), 0, 1),
        "salt": np.clip(get("evaporite") + 0.4 * get("aridity"), 0, 1),
        "dimension_stone": np.clip(access * get("stable") * (1.0 - get("sediment")), 0, 1),
    }


def generate_deposits(
    context: DepositContext, seed: int
) -> tuple[list[Deposit], dict[str, np.ndarray]]:
    rng = np.random.default_rng(seed + 104729)
    deposits: list[Deposit] = []
    serial = 0
    for spec in DEPOSIT_CATALOG:
        arrays = [context.factors.get(name, np.zeros(context.size)) for name in spec.factors]
        suitability = _geologic_and(arrays)
        host = suitability > 0.14
        if spec.offshore:
            host &= context.land | (context.water_depth < 1200.0)
        else:
            host &= context.land
        weights = np.where(host, context.area_km2 * suitability**3, 0.0)
        expected = (
            8.0
            * spec.rate_per_million_km2
            * float(weights.sum())
            / 1_000_000.0
        )
        count = int(rng.poisson(expected))
        if weights.sum() <= 0:
            continue
        # The global map is conditioned on showing every important class when
        # the simulated planet actually contains a valid host. This does not
        # fabricate deposits in zero-suitability geology.
        count = max(1, count)
        count = min(count, int(np.count_nonzero(weights)), 80)
        probabilities = weights / weights.sum()
        chosen = rng.choice(context.size, size=count, replace=False, p=probabilities)
        for cell in chosen:
            score = float(suitability[cell])
            tonnage = float(
                rng.lognormal(np.log(spec.median_tonnage) + 0.8 * (score - 0.5), 0.8)
            )
            grade_value = float(
                spec.median_grade
                * rng.lognormal(0.25 * (score - 0.5), 0.28)
                * (spec.median_tonnage / max(tonnage, 1.0)) ** 0.06
            )
            depth = float(
                np.clip(
                    rng.lognormal(
                        np.log(120.0 + 650.0 * context.factors.get("basin", np.zeros(context.size))[cell])
                        - 0.5 * context.factors.get("exhumation", np.zeros(context.size))[cell],
                        0.65,
                    ),
                    0.0,
                    7000.0,
                )
            )
            accessibility = float(
                np.clip(
                    1.0
                    - 0.48 * context.ruggedness[cell]
                    - 0.30 * context.slope[cell]
                    - 0.35 * min(context.water_depth[cell] / 1500.0, 1.0)
                    - 0.22 * context.water_stress[cell],
                    0,
                    1,
                )
            )
            difficulty = float(
                np.clip(
                    spec.processing_base
                    + 0.15 * context.water_stress[cell]
                    + 0.12 * context.ruggedness[cell]
                    + rng.normal(0, 0.06),
                    0,
                    1,
                )
            )
            recovery = float(np.clip(0.92 * (1.0 - 0.5 * difficulty), 0.25, 0.95))
            economic_fraction = float(
                1.0
                / (
                    1.0
                    + np.exp(
                        -4.0
                        * (
                            score
                            + 0.35 * accessibility
                            - 0.45 * difficulty
                            - 0.42
                        )
                    )
                )
            )
            deposits.append(
                Deposit(
                    id=f"{spec.id}-{serial}",
                    deposit_class=spec.id,
                    name=spec.display_name,
                    lon=float(context.lon_deg[cell]),
                    lat=float(context.lat_deg[cell]),
                    prospect_score=score,
                    ore_resource_t=tonnage,
                    grade={spec.grade_key: grade_value},
                    depth_m=depth,
                    accessibility=accessibility,
                    processing_difficulty=difficulty,
                    recovery=recovery,
                    reserve_2025_t=tonnage * recovery * economic_fraction,
                    byproducts=spec.byproducts,
                )
            )
            serial += 1
    return deposits, _bulk_materials(context)
