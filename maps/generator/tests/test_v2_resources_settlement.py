import unittest

import numpy as np

from deeptime.v2.resources import DepositContext, generate_deposits
from deeptime.v2.settlement import (
    IncentiveFields,
    SettlementInputs,
    compute_settlement,
)


class ResourceTests(unittest.TestCase):
    def test_absent_geological_host_produces_no_deposit(self) -> None:
        context = DepositContext.zeros(128)
        deposits, _ = generate_deposits(context, seed=1)
        self.assertEqual(deposits, [])

    def test_counts_are_not_pinned_to_fourteen(self) -> None:
        context = DepositContext.synthetic_hosted(512)
        counts = []
        for seed in range(8):
            deposits, _ = generate_deposits(context, seed=seed)
            counts.append(len(deposits))
        self.assertGreater(len(set(counts)), 1)
        self.assertNotEqual(set(counts), {14})

    def test_properties_are_physical_and_reserve_is_bounded(self) -> None:
        context = DepositContext.synthetic_hosted(512)
        deposits, _ = generate_deposits(context, seed=42)
        self.assertGreater(len(deposits), 0)
        for deposit in deposits:
            self.assertGreater(deposit.ore_resource_t, 0)
            self.assertGreaterEqual(deposit.depth_m, 0)
            self.assertGreaterEqual(deposit.processing_difficulty, 0)
            self.assertLessEqual(deposit.processing_difficulty, 1)
            self.assertLessEqual(deposit.reserve_2025_t, deposit.ore_resource_t)


class SettlementTests(unittest.TestCase):
    def _base(self) -> SettlementInputs:
        n = 3
        return SettlementInputs(
            land=np.ones(n, dtype=bool),
            temperature_c=np.array([29.0, 16.0, 29.0]),
            hottest_wet_bulb_c=np.array([31.0, 19.0, 31.0]),
            coldest_month_c=np.array([20.0, 4.0, 20.0]),
            humidity=np.array([0.8, 0.45, 0.8]),
            water=np.array([0.55, 0.8, 0.2]),
            food=np.array([0.6, 0.8, 0.1]),
            buildability=np.array([0.7, 0.8, 0.2]),
            disease_safety=np.array([0.55, 0.85, 0.85]),
            hazard_safety=np.array([0.8, 0.85, 0.6]),
            grid_reliability=np.array([0.0, 1.0, 0.0]),
            capital_access=np.ones(n),
            energy_headroom=np.ones(n),
            cdd24=np.array([2200.0, 20.0, 2200.0]),
            outdoor_labor_share=np.array([0.2, 0.2, 0.6]),
            service_energy=np.ones(n),
            service_water=np.ones(n),
            service_food=np.ones(n),
            logistics_access=np.ones(n),
        )

    def test_no_grid_means_no_air_conditioning_uplift(self) -> None:
        inputs = self._base()
        result = compute_settlement(inputs, IncentiveFields.zeros(3))
        self.assertAlmostEqual(float(result.h_ac[0]), float(result.h_ind[0]), places=10)

    def test_air_conditioning_uplifts_hot_humid_not_temperate(self) -> None:
        inputs = self._base()
        inputs.grid_reliability[0] = 0.95
        result = compute_settlement(inputs, IncentiveFields.zeros(3))
        self.assertGreater(float(result.h_ac[0] - result.h_ind[0]), 0.1)
        self.assertLess(abs(float(result.h_ac[1] - result.h_ind[1])), 0.02)
        self.assertGreater(float(result.ac_energy_served_kwh_pc_yr[0]), 1000)

    def test_incentive_can_override_marginal_habitability(self) -> None:
        inputs = self._base()
        incentives = IncentiveFields.zeros(3)
        incentives.resource[2] = 0.45
        incentives.strategy[2] = 0.95
        incentives.policy[2] = 0.2
        result = compute_settlement(inputs, incentives)
        self.assertLess(float(result.h_ind[2]), 0.4)
        self.assertLess(float(result.settle_ind_no_incentive[2]), 0.4)
        self.assertGreaterEqual(float(result.settle_ind[2]), 0.4)
        self.assertEqual(result.mechanism_ind[2], "incentive_driven")

    def test_incentives_do_not_change_physical_habitability(self) -> None:
        inputs = self._base()
        none = compute_settlement(inputs, IncentiveFields.zeros(3))
        incentives = IncentiveFields.zeros(3)
        incentives.trade[:] = 1.0
        incentives.policy[:] = 1.0
        driven = compute_settlement(inputs, incentives)
        np.testing.assert_allclose(none.h_pre, driven.h_pre)
        np.testing.assert_allclose(none.h_ind, driven.h_ind)
        np.testing.assert_allclose(none.h_ac, driven.h_ac)


if __name__ == "__main__":
    unittest.main()
