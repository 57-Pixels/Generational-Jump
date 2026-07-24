"""Technology-era habitability and incentive-driven settlement."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SettlementInputs:
    land: np.ndarray
    temperature_c: np.ndarray
    hottest_wet_bulb_c: np.ndarray
    coldest_month_c: np.ndarray
    humidity: np.ndarray
    water: np.ndarray
    food: np.ndarray
    buildability: np.ndarray
    disease_safety: np.ndarray
    hazard_safety: np.ndarray
    grid_reliability: np.ndarray
    capital_access: np.ndarray
    energy_headroom: np.ndarray
    cdd24: np.ndarray
    outdoor_labor_share: np.ndarray
    service_energy: np.ndarray
    service_water: np.ndarray
    service_food: np.ndarray
    logistics_access: np.ndarray


@dataclass
class IncentiveFields:
    resource: np.ndarray
    trade: np.ndarray
    strategy: np.ndarray
    policy: np.ndarray
    institutional: np.ndarray

    @classmethod
    def zeros(cls, size: int) -> "IncentiveFields":
        return cls(*(np.zeros(size, dtype=np.float64) for _ in range(5)))


@dataclass
class SettlementFields:
    h_pre: np.ndarray
    h_ind: np.ndarray
    h_ac: np.ndarray
    ac_feasibility: np.ndarray
    ac_energy_full_kwh_pc_yr: np.ndarray
    ac_energy_served_kwh_pc_yr: np.ndarray
    ac_water_l_pc_day: np.ndarray
    incentive_intensity: np.ndarray
    dominant_incentive: np.ndarray
    service_burden: np.ndarray
    settle_ind_no_incentive: np.ndarray
    settle_ind: np.ndarray
    settle_ac: np.ndarray
    support_ac: np.ndarray
    mechanism_ind: np.ndarray
    mechanism_ac: np.ndarray


def _weighted_geometric(values: list[np.ndarray], weights: list[float]) -> np.ndarray:
    stacked = np.stack([np.clip(value, 0.02, 1.0) for value in values], axis=0)
    weight = np.asarray(weights, dtype=np.float64)[:, None]
    return np.exp(np.sum(weight * np.log(stacked), axis=0) / weight.sum())


def _logit(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, 1e-6, 1.0 - 1e-6)
    return np.log(clipped / (1.0 - clipped))


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))


def _mechanism(
    habitability: np.ndarray,
    no_incentive: np.ndarray,
    attraction: np.ndarray,
    technology_uplift: np.ndarray,
) -> np.ndarray:
    result = np.full(len(habitability), "mixed", dtype=object)
    incentive_driven = (
        (habitability < 0.4) & (no_incentive < 0.4) & (attraction >= 0.4)
    )
    technology_enabled = (technology_uplift >= 0.1) & (attraction >= 0.4)
    result[(attraction < 0.4)] = "nonviable"
    result[(habitability >= 0.6) & (attraction >= 0.4)] = "environment_led"
    result[incentive_driven] = "incentive_driven"
    result[technology_enabled] = "technology_enabled"
    result[incentive_driven & technology_enabled] = "combined"
    return result


def compute_settlement(
    inputs: SettlementInputs,
    incentives: IncentiveFields,
) -> SettlementFields:
    land = np.asarray(inputs.land, dtype=bool)
    wet_bulb = np.asarray(inputs.hottest_wet_bulb_c, dtype=np.float64)
    coldest = np.asarray(inputs.coldest_month_c, dtype=np.float64)
    hot_pre = np.exp(-(np.maximum(0.0, wet_bulb - 22.0) / 6.0) ** 2)
    hot_ind = np.exp(-(np.maximum(0.0, wet_bulb - 24.0) / 7.0) ** 2)
    cold_pre = np.exp(-(np.maximum(0.0, -10.0 - coldest) / 14.0) ** 2)
    cold_ind = np.exp(-(np.maximum(0.0, -20.0 - coldest) / 18.0) ** 2)
    thermal_pre = hot_pre * cold_pre
    thermal_ind = hot_ind * cold_ind

    common = [
        np.clip(inputs.water, 0, 1),
        np.clip(inputs.food, 0, 1),
        np.clip(inputs.buildability, 0, 1),
        np.clip(inputs.disease_safety, 0, 1),
        np.clip(inputs.hazard_safety, 0, 1),
    ]
    h_pre = _weighted_geometric(
        [thermal_pre, *common], [0.18, 0.25, 0.27, 0.12, 0.10, 0.08]
    )
    h_ind = _weighted_geometric(
        [thermal_ind, *common], [0.30, 0.22, 0.12, 0.13, 0.10, 0.13]
    )

    ac_feasibility = np.minimum.reduce(
        [
            np.clip(inputs.grid_reliability, 0, 1),
            np.clip(inputs.capital_access, 0, 1),
            np.clip(inputs.energy_headroom, 0, 1),
        ]
    )
    outdoor = np.clip(inputs.outdoor_labor_share, 0, 1)
    indoor_hot = hot_ind + ac_feasibility * (1.0 - hot_ind)
    hot_ac = outdoor * hot_ind + (1.0 - outdoor) * indoor_hot
    thermal_ac = hot_ac * cold_ind
    h_ac = _weighted_geometric(
        [thermal_ac, *common], [0.30, 0.22, 0.12, 0.13, 0.10, 0.13]
    )

    energy_full = (
        900.0
        * np.asarray(inputs.cdd24)
        / 1000.0
        * (1.0 + 0.7 * np.clip(inputs.humidity, 0, 1))
        * (3.0 / 3.2)
    )
    energy_served = ac_feasibility * energy_full
    water_l_day = energy_served * 0.7 / 365.0

    resource = np.clip(incentives.resource, 0, 1)
    trade = np.clip(incentives.trade, 0, 1)
    strategy = np.clip(incentives.strategy, 0, 1)
    policy = np.clip(incentives.policy, 0, 1)
    institutional = np.clip(incentives.institutional, 0, 1)
    incentive_intensity = 1.0 - (
        (1.0 - resource)
        * (1.0 - trade)
        * (1.0 - strategy)
        * (1.0 - policy)
        * (1.0 - institutional)
    )
    contributions = np.stack(
        (2.0 * resource, 2.2 * trade, 1.6 * strategy, 2.0 * policy, 1.4 * institutional),
        axis=0,
    )
    names = np.array(["resource", "trade", "strategy", "policy", "institutional"])
    dominant = names[np.argmax(contributions, axis=0)]
    bonus = np.clip(contributions.sum(axis=0), 0, 4.5)

    burden = (
        1.2 * (1.0 - np.clip(inputs.service_energy, 0, 1))
        + 1.5 * (1.0 - np.clip(inputs.service_water, 0, 1))
        + 0.8 * (1.0 - np.clip(inputs.service_food, 0, 1))
        + 0.5 * (1.0 - np.clip(inputs.logistics_access, 0, 1))
    )
    settle_ind_no = _sigmoid(_logit(h_ind) - burden)
    settle_ind = _sigmoid(_logit(h_ind) + bonus - burden)
    settle_ac = _sigmoid(_logit(h_ac) + bonus - burden)

    for array in (h_pre, h_ind, h_ac, settle_ind_no, settle_ind, settle_ac):
        array[~land] = 0.0
    ac_feasibility[~land] = 0.0
    energy_full[~land] = 0.0
    energy_served[~land] = 0.0
    water_l_day[~land] = 0.0
    mechanism_ind = _mechanism(h_ind, settle_ind_no, settle_ind, np.zeros_like(h_ind))
    mechanism_ac = _mechanism(h_ac, settle_ind_no, settle_ac, h_ac - h_ind)
    mechanism_ind[~land] = "impossible"
    mechanism_ac[~land] = "impossible"
    return SettlementFields(
        h_pre=h_pre,
        h_ind=h_ind,
        h_ac=h_ac,
        ac_feasibility=ac_feasibility,
        ac_energy_full_kwh_pc_yr=energy_full,
        ac_energy_served_kwh_pc_yr=energy_served,
        ac_water_l_pc_day=water_l_day,
        incentive_intensity=incentive_intensity,
        dominant_incentive=dominant,
        service_burden=burden,
        settle_ind_no_incentive=settle_ind_no,
        settle_ind=settle_ind,
        settle_ac=settle_ac,
        support_ac=np.where(land, h_ac**1.5, 0.0),
        mechanism_ind=mechanism_ind,
        mechanism_ac=mechanism_ac,
    )
