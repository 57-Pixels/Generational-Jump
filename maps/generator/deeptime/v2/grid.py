"""Cubed-sphere computational grid and equirectangular reprojection."""

from __future__ import annotations

from dataclasses import dataclass, field
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

_NEIGHBOR_OFFSETS = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
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


def _build_neighbors(n: int, alpha: np.ndarray, beta: np.ndarray, delta: float) -> np.ndarray:
    """Dense (N, 8) neighbour table via extended face coordinates.

    Prototyped against the legacy set-based builder: set-identical at every
    tested ``n``, and already fully symmetric, so no repair pass is needed.
    """
    size = 6 * n * n
    neighbors = np.full((size, 8), -1, dtype=np.int32)
    for slot, (di, dj) in enumerate(_NEIGHBOR_OFFSETS):
        aa = alpha + di * delta
        bb = beta + dj * delta
        for face in range(6):
            target = CubedSphere.indices_for_xyz_static(
                _face_vectors(face, aa, bb).reshape(-1, 3), n
            )
            neighbors[face * n * n : (face + 1) * n * n, slot] = target
    self_ref = neighbors == np.arange(size, dtype=np.int32)[:, None]
    neighbors[self_ref] = -1
    # Corner cells can map two offsets onto the same neighbour. Compact to
    # unique ids so degree matches the undirected graph (24 cells of degree 7).
    sentinel = np.iinfo(np.int32).max
    keyed = np.where(neighbors >= 0, neighbors, sentinel)
    order = np.argsort(keyed, axis=1)
    sorted_nb = np.take_along_axis(neighbors, order, axis=1)
    duplicate = np.zeros_like(sorted_nb, dtype=bool)
    duplicate[:, 1:] = (sorted_nb[:, 1:] == sorted_nb[:, :-1]) & (sorted_nb[:, 1:] >= 0)
    sorted_nb[duplicate] = -1
    compact_key = np.where(sorted_nb >= 0, 0, 1)
    compact_order = np.argsort(compact_key, axis=1, kind="stable")
    return np.take_along_axis(sorted_nb, compact_order, axis=1)


@dataclass
class CubedSphere:
    n: int
    xyz: np.ndarray
    area_sr: np.ndarray
    neighbors: np.ndarray
    _edge_cells: np.ndarray | None = field(default=None, repr=False, compare=False)
    _lon_deg: np.ndarray | None = field(default=None, repr=False, compare=False)
    _lat_deg: np.ndarray | None = field(default=None, repr=False, compare=False)

    @property
    def size(self) -> int:
        return int(self.xyz.shape[0])

    @property
    def lon_deg(self) -> np.ndarray:
        if self._lon_deg is None:
            self._lon_deg = np.rad2deg(np.arctan2(self.xyz[:, 1], self.xyz[:, 0]))
        return self._lon_deg

    @property
    def lat_deg(self) -> np.ndarray:
        if self._lat_deg is None:
            self._lat_deg = np.rad2deg(
                np.arcsin(np.clip(self.xyz[:, 2], -1.0, 1.0))
            )
        return self._lat_deg

    @property
    def edge_cells(self) -> np.ndarray:
        """Undirected unique neighbour pairs. Built lazily — never at T1."""
        if self._edge_cells is None:
            valid = self.neighbors >= 0
            src = np.repeat(
                np.arange(self.size, dtype=np.int32), self.neighbors.shape[1]
            )
            dst = self.neighbors.ravel()
            mask = valid.ravel() & (src < dst)
            self._edge_cells = np.stack((src[mask], dst[mask]), axis=1)
        return self._edge_cells

    @classmethod
    @lru_cache(maxsize=2)
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
        neighbors = _build_neighbors(n, alpha, beta, delta)

        return cls(
            n=n,
            xyz=xyz,
            area_sr=area_sr,
            neighbors=neighbors,
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
        # Circular with topology.component_labels; import deferred by design.
        from .topology import component_labels

        labels = component_labels(self, mask)
        if not np.any(labels >= 0):
            return []
        count = int(labels.max()) + 1
        return [
            np.flatnonzero(labels == label).astype(np.int32)
            for label in range(count)
        ]

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
        self,
        field: np.ndarray,
        width: int = 1024,
        height: int = 512,
        *,
        blend: bool | None = None,
        blend_power: float = 6.0,
    ) -> np.ndarray:
        """Sample ``field`` onto an equirectangular image.

        When ``blend`` is true (default for floating fields), each pixel is a
        spherical weight of the nearest cell and its neighbours so cell edges
        do not print as hard squares.
        """
        lon = np.linspace(-np.pi, np.pi, width, endpoint=False)
        lat = (
            np.linspace(np.pi / 2, -np.pi / 2, height, endpoint=False)
            - np.pi / (2 * height)
        )
        llon, llat = np.meshgrid(lon, lat)
        xyz = np.stack(
            (
                np.cos(llat) * np.cos(llon),
                np.cos(llat) * np.sin(llon),
                np.sin(llat),
            ),
            axis=-1,
        )
        flat_xyz = xyz.reshape(-1, 3)
        index = self.indices_for_xyz(flat_xyz)
        values = np.asarray(field)
        if blend is None:
            blend = bool(np.issubdtype(values.dtype, np.floating))
        if not blend:
            return values[index].reshape((height, width) + values.shape[1:])

        # Promote to float for weighted blend; cast back for float32 inputs.
        sample = values.astype(np.float64, copy=False)
        multi = sample.ndim > 1
        if not multi:
            sample = sample[:, None]

        n_pix = flat_xyz.shape[0]
        accum = np.zeros((n_pix, sample.shape[1]), dtype=np.float64)
        weight = np.zeros(n_pix, dtype=np.float64)

        def _accumulate(cell_idx: np.ndarray, mask: np.ndarray) -> None:
            if not np.any(mask):
                return
            dots = np.sum(flat_xyz[mask] * self.xyz[cell_idx[mask]], axis=1)
            w = np.maximum(dots, 0.0) ** blend_power
            accum[mask] += w[:, None] * sample[cell_idx[mask]]
            weight[mask] += w

        _accumulate(index, np.ones(n_pix, dtype=bool))
        neigh = self.neighbors[index]
        for slot in range(neigh.shape[1]):
            cells = neigh[:, slot]
            _accumulate(cells, cells >= 0)

        # Degenerate poles / cracks: fall back to nearest.
        bare = weight < 1e-12
        if np.any(bare):
            accum[bare] = sample[index[bare]]
            weight[bare] = 1.0
        out = accum / weight[:, None]
        shaped = out.reshape((height, width, sample.shape[1]))
        if not multi:
            shaped = shaped[..., 0]
        if values.dtype == np.float32:
            return shaped.astype(np.float32)
        return shaped
