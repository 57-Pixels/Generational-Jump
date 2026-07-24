"""Cubed-sphere computational grid and equirectangular reprojection."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

_FACE_C = np.array(
    [
        [1.0, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, -1.0],
    ]
)
_FACE_EU = np.array(
    [
        [0.0, 1.0, 0.0],
        [0.0, -1.0, 0.0],
        [-1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
    ]
)
_FACE_EV = np.array(
    [
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        [-1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    ]
)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.maximum(np.linalg.norm(vectors, axis=-1, keepdims=True), 1e-15)


def _face_vectors(face: int, alpha: np.ndarray, beta: np.ndarray) -> np.ndarray:
    raw = (
        _FACE_C[face]
        + np.tan(alpha)[..., None] * _FACE_EU[face]
        + np.tan(beta)[..., None] * _FACE_EV[face]
    )
    return _normalize(raw)


def _triangle_area(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    numerator = np.abs(np.einsum("...i,...i->...", a, np.cross(b, c)))
    denominator = (
        1.0
        + np.einsum("...i,...i->...", a, b)
        + np.einsum("...i,...i->...", b, c)
        + np.einsum("...i,...i->...", c, a)
    )
    return 2.0 * np.arctan2(numerator, denominator)


@dataclass(frozen=True)
class CubedSphere:
    n: int
    xyz: np.ndarray
    area_sr: np.ndarray
    neighbors: np.ndarray
    edge_cells: np.ndarray
    lon_deg: np.ndarray
    lat_deg: np.ndarray

    @property
    def size(self) -> int:
        return int(self.xyz.shape[0])

    @classmethod
    @lru_cache(maxsize=12)
    def create(cls, n: int) -> "CubedSphere":
        if n < 4:
            raise ValueError("cubed-sphere face resolution must be >= 4")
        delta = (np.pi / 2.0) / n
        centers = -np.pi / 4.0 + (np.arange(n) + 0.5) * delta
        edges = -np.pi / 4.0 + np.arange(n + 1) * delta
        alpha, beta = np.meshgrid(centers, centers, indexing="xy")
        a0, b0 = np.meshgrid(edges[:-1], edges[:-1], indexing="xy")
        a1, b1 = np.meshgrid(edges[1:], edges[1:], indexing="xy")

        faces: list[np.ndarray] = []
        areas: list[np.ndarray] = []
        for face in range(6):
            center_xyz = _face_vectors(face, alpha, beta)
            p00 = _face_vectors(face, a0, b0)
            p10 = _face_vectors(face, a1, b0)
            p11 = _face_vectors(face, a1, b1)
            p01 = _face_vectors(face, a0, b1)
            area = _triangle_area(p00, p10, p11) + _triangle_area(p00, p11, p01)
            faces.append(center_xyz.reshape(-1, 3))
            areas.append(area.ravel())

        xyz = np.concatenate(faces, axis=0)
        area_sr = np.concatenate(areas)
        area_sr *= (4.0 * np.pi) / float(area_sr.sum())

        # Build eight-neighbor candidate graph, then symmetrize it. Extended
        # face coordinates naturally cross cube seams before inverse mapping.
        source = np.arange(6 * n * n, dtype=np.int32).reshape(6, n, n)
        pairs: list[np.ndarray] = []
        for di, dj in (
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ):
            aa = alpha + di * delta
            bb = beta + dj * delta
            for face in range(6):
                target_xyz = _face_vectors(face, aa, bb).reshape(-1, 3)
                target = cls.indices_for_xyz_static(target_xyz, n)
                src = source[face].ravel()
                pair = np.stack((np.minimum(src, target), np.maximum(src, target)), axis=1)
                pairs.append(pair[pair[:, 0] != pair[:, 1]])
        edge_cells = np.unique(np.concatenate(pairs, axis=0), axis=0).astype(np.int32)

        adjacency: list[set[int]] = [set() for _ in range(6 * n * n)]
        for left, right in edge_cells:
            adjacency[int(left)].add(int(right))
            adjacency[int(right)].add(int(left))
        max_degree = max(len(items) for items in adjacency)
        neighbors = np.full((6 * n * n, max_degree), -1, dtype=np.int32)
        for cell, items in enumerate(adjacency):
            ordered = sorted(items)
            neighbors[cell, : len(ordered)] = ordered

        lon_deg = np.rad2deg(np.arctan2(xyz[:, 1], xyz[:, 0]))
        lat_deg = np.rad2deg(np.arcsin(np.clip(xyz[:, 2], -1.0, 1.0)))
        return cls(
            n=n,
            xyz=xyz,
            area_sr=area_sr,
            neighbors=neighbors,
            edge_cells=edge_cells,
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )

    @staticmethod
    def indices_for_xyz_static(xyz: np.ndarray, n: int) -> np.ndarray:
        xyz = _normalize(np.asarray(xyz, dtype=np.float64))
        dominant = np.argmax(np.abs(xyz), axis=1)
        face = np.empty(len(xyz), dtype=np.int32)
        face[(dominant == 0) & (xyz[:, 0] >= 0)] = 0
        face[(dominant == 0) & (xyz[:, 0] < 0)] = 1
        face[(dominant == 1) & (xyz[:, 1] >= 0)] = 2
        face[(dominant == 1) & (xyz[:, 1] < 0)] = 3
        face[(dominant == 2) & (xyz[:, 2] >= 0)] = 4
        face[(dominant == 2) & (xyz[:, 2] < 0)] = 5

        i = np.empty(len(xyz), dtype=np.int32)
        j = np.empty(len(xyz), dtype=np.int32)
        for f in range(6):
            mask = face == f
            if not np.any(mask):
                continue
            denom = xyz[mask] @ _FACE_C[f]
            u = (xyz[mask] @ _FACE_EU[f]) / np.maximum(denom, 1e-15)
            v = (xyz[mask] @ _FACE_EV[f]) / np.maximum(denom, 1e-15)
            alpha = np.arctan(u)
            beta = np.arctan(v)
            i[mask] = np.clip(((alpha + np.pi / 4) / (np.pi / 2) * n).astype(int), 0, n - 1)
            j[mask] = np.clip(((beta + np.pi / 4) / (np.pi / 2) * n).astype(int), 0, n - 1)
        return face * (n * n) + j * n + i

    def indices_for_xyz(self, xyz: np.ndarray) -> np.ndarray:
        return self.indices_for_xyz_static(xyz, self.n)

    def components(self, mask: np.ndarray) -> list[np.ndarray]:
        mask = np.asarray(mask, dtype=bool)
        seen = np.zeros(self.size, dtype=bool)
        result: list[np.ndarray] = []
        for start in np.flatnonzero(mask):
            if seen[start]:
                continue
            stack = [int(start)]
            seen[start] = True
            cells: list[int] = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                for neighbor in self.neighbors[cell]:
                    if neighbor < 0:
                        continue
                    n = int(neighbor)
                    if mask[n] and not seen[n]:
                        seen[n] = True
                        stack.append(n)
            result.append(np.asarray(cells, dtype=np.int32))
        return sorted(result, key=len, reverse=True)

    def smooth(self, field: np.ndarray, iterations: int = 1, self_weight: float = 2.0) -> np.ndarray:
        out = np.asarray(field, dtype=np.float64).copy()
        valid = self.neighbors >= 0
        safe = np.where(valid, self.neighbors, 0)
        for _ in range(iterations):
            total = np.where(valid, out[safe], 0.0).sum(axis=1)
            count = valid.sum(axis=1)
            out = (self_weight * out + total) / (self_weight + count)
        return out

    def to_equirect(
        self, field: np.ndarray, width: int = 1024, height: int = 512
    ) -> np.ndarray:
        lon = np.linspace(-np.pi, np.pi, width, endpoint=False)
        lat = np.linspace(np.pi / 2, -np.pi / 2, height, endpoint=False) - np.pi / (2 * height)
        llon, llat = np.meshgrid(lon, lat)
        xyz = np.stack(
            (
                np.cos(llat) * np.cos(llon),
                np.cos(llat) * np.sin(llon),
                np.sin(llat),
            ),
            axis=-1,
        )
        index = self.indices_for_xyz(xyz.reshape(-1, 3))
        values = np.asarray(field)
        return values[index].reshape((height, width) + values.shape[1:])
