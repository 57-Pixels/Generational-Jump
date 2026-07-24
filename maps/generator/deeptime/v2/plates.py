"""Rigid spherical plates and signed boundary kinematics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import CubedSphere

BOUNDARY_INACTIVE = 0
BOUNDARY_DIVERGENT = 1
BOUNDARY_CONVERGENT = 2
BOUNDARY_TRANSFORM = 3
EARTH_RADIUS_KM = 6371.0


def _normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.maximum(np.linalg.norm(vectors, axis=-1, keepdims=True), 1e-15)


def rodrigues_rotate(points: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    axis = np.asarray(axis, dtype=np.float64)
    norm = float(np.linalg.norm(axis))
    if norm < 1e-15 or abs(angle) < 1e-15:
        return points.copy()
    k = axis / norm
    cosine = np.cos(angle)
    sine = np.sin(angle)
    rotated = (
        points * cosine
        + np.cross(k, points) * sine
        + np.outer(points @ k, k) * (1.0 - cosine)
    )
    return _normalize(rotated)


@dataclass
class BoundaryFields:
    edge_cells: np.ndarray
    plate_a: np.ndarray
    plate_b: np.ndarray
    opening_km_ma: np.ndarray
    shear_km_ma: np.ndarray
    kind: np.ndarray


@dataclass
class PlateModel:
    seed_xyz: np.ndarray
    omega_xyz: np.ndarray
    plate_id: np.ndarray

    @classmethod
    def initialize(
        cls, grid: CubedSphere, n_plates: int = 12, seed: int = 42
    ) -> "PlateModel":
        if n_plates < 2:
            raise ValueError("at least two plates are required")
        rng = np.random.default_rng(seed)
        candidates = _normalize(rng.normal(size=(max(1000, n_plates * 200), 3)))
        chosen = [int(rng.integers(len(candidates)))]
        best_dot = candidates @ candidates[chosen[0]]
        for _ in range(1, n_plates):
            next_index = int(np.argmin(best_dot))
            chosen.append(next_index)
            best_dot = np.maximum(best_dot, candidates @ candidates[next_index])
        seeds = candidates[chosen]

        # Euler vectors: ~5–35 km/Ma surface speeds (mm/year).
        poles = _normalize(rng.normal(size=(n_plates, 3)))
        rates = rng.uniform(5.0, 35.0, size=n_plates) / EARTH_RADIUS_KM
        omega = poles * rates[:, None]
        omega -= omega.mean(axis=0, keepdims=True)
        labels = cls.labels_for(grid.xyz, seeds)
        model = cls(seed_xyz=seeds, omega_xyz=omega, plate_id=labels)
        model.assert_connected(grid)
        return model

    @classmethod
    def two_plate_fixture(
        cls, grid: CubedSphere, opening_km_ma: float
    ) -> "PlateModel":
        seeds = np.array([[0.0, -1.0, 0.0], [0.0, 1.0, 0.0]])
        rate = opening_km_ma / (2.0 * EARTH_RADIUS_KM)
        omega = np.array([[0.0, 0.0, -rate], [0.0, 0.0, rate]])
        return cls(seeds, omega, cls.labels_for(grid.xyz, seeds))

    @staticmethod
    def labels_for(xyz: np.ndarray, seeds: np.ndarray) -> np.ndarray:
        return np.argmax(np.asarray(xyz) @ np.asarray(seeds).T, axis=1).astype(np.int32)

    def velocity_km_ma(self, xyz: np.ndarray, plate_ids: np.ndarray) -> np.ndarray:
        return EARTH_RADIUS_KM * np.cross(self.omega_xyz[plate_ids], xyz)

    def advance(self, grid: CubedSphere, dt_ma: float) -> None:
        moved = np.empty_like(self.seed_xyz)
        for plate in range(len(self.seed_xyz)):
            rate = float(np.linalg.norm(self.omega_xyz[plate]))
            moved[plate] = rodrigues_rotate(
                self.seed_xyz[plate : plate + 1],
                self.omega_xyz[plate],
                rate * dt_ma,
            )[0]
        self.seed_xyz = moved
        self.plate_id = self.labels_for(grid.xyz, self.seed_xyz)

    def boundaries(self, grid: CubedSphere, threshold_km_ma: float = 2.0) -> BoundaryFields:
        edges = grid.edge_cells
        left = edges[:, 0]
        right = edges[:, 1]
        different = self.plate_id[left] != self.plate_id[right]
        active_edges = edges[different]
        if len(active_edges) == 0:
            empty_i = np.empty(0, dtype=np.int32)
            empty_f = np.empty(0, dtype=np.float64)
            return BoundaryFields(active_edges, empty_i, empty_i, empty_f, empty_f, empty_i)

        ids_left = self.plate_id[active_edges[:, 0]]
        ids_right = self.plate_id[active_edges[:, 1]]
        plate_a = np.minimum(ids_left, ids_right)
        plate_b = np.maximum(ids_left, ids_right)
        midpoint = _normalize(grid.xyz[active_edges[:, 0]] + grid.xyz[active_edges[:, 1]])

        delta_seed = self.seed_xyz[plate_b] - self.seed_xyz[plate_a]
        normal = delta_seed - np.einsum("ij,ij->i", delta_seed, midpoint)[:, None] * midpoint
        normal = _normalize(normal)
        tangent = _normalize(np.cross(midpoint, normal))

        va = EARTH_RADIUS_KM * np.cross(self.omega_xyz[plate_a], midpoint)
        vb = EARTH_RADIUS_KM * np.cross(self.omega_xyz[plate_b], midpoint)
        relative = vb - va
        opening = np.einsum("ij,ij->i", relative, normal)
        shear = np.einsum("ij,ij->i", relative, tangent)

        kind = np.full(len(active_edges), BOUNDARY_INACTIVE, dtype=np.int32)
        transform = (np.abs(opening) < np.maximum(threshold_km_ma, 0.35 * np.abs(shear))) & (
            np.abs(shear) >= threshold_km_ma
        )
        kind[transform] = BOUNDARY_TRANSFORM
        kind[(~transform) & (opening >= threshold_km_ma)] = BOUNDARY_DIVERGENT
        kind[(~transform) & (opening <= -threshold_km_ma)] = BOUNDARY_CONVERGENT
        return BoundaryFields(
            edge_cells=active_edges,
            plate_a=plate_a,
            plate_b=plate_b,
            opening_km_ma=opening,
            shear_km_ma=shear,
            kind=kind,
        )

    def assert_connected(self, grid: CubedSphere) -> None:
        for plate in range(len(self.seed_xyz)):
            components = grid.components(self.plate_id == plate)
            if len(components) != 1:
                raise AssertionError(
                    f"plate {plate} has {len(components)} disconnected components"
                )
