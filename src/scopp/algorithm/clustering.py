"""SCoPP clustering orchestration and conflict-cell identification."""

from __future__ import annotations

from dataclasses import dataclass

from scopp.algorithm.clustering_profiles import get_clusterer, lloyd_cluster
from scopp.config import ClusteringProfile
from scopp.map.models import DiscretizedMap, XY


@dataclass(frozen=True, slots=True)
class Cluster:
    index: int
    node_id: str
    centroid: XY
    sample_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CellClusterAssignment:
    cell_id: str
    cluster_indices: tuple[int, ...]

    @property
    def is_conflict(self) -> bool:
        return len(self.cluster_indices) > 1


@dataclass(frozen=True, slots=True)
class ClusteringResult:
    clusters: tuple[Cluster, ...]
    sample_points: tuple[XY, ...]
    sample_labels: tuple[int, ...]
    cell_assignments: tuple[CellClusterAssignment, ...]
    iterations: int
    converged: bool
    tolerance_m: float
    profile: str = ClusteringProfile.OFFICIAL_MINIBATCH.value
    random_seed: int | None = None

    @property
    def conflict_cell_ids(self) -> tuple[str, ...]:
        return tuple(item.cell_id for item in self.cell_assignments if item.is_conflict)


def cluster_map(
    value: DiscretizedMap,
    *,
    tolerance_m: float | None = None,
    max_iterations: int = 10,
    profile: ClusteringProfile | str = ClusteringProfile.OFFICIAL_MINIBATCH,
    random_seed: int = 0,
) -> ClusteringResult:
    """Apply a selected clustering strategy and identify conflict cells."""
    if not value.source.node_starts:
        raise ValueError("SCoPP clustering requires at least one node")
    points = tuple(point for cell in value.cells for point in cell.perimeter_samples)
    tolerance = tolerance_m if tolerance_m is not None else value.cell_width_m / 8.0
    clusterer = get_clusterer(profile)
    raw = clusterer.fit(points, value.source.node_starts, tolerance_m=tolerance, max_iterations=max_iterations, random_seed=random_seed)
    clusters = tuple(
        Cluster(index, raw.node_ids[index], centroid, tuple(i for i, label in enumerate(raw.labels) if label == index))
        for index, centroid in enumerate(raw.centroids)
    )
    assignments: list[CellClusterAssignment] = []
    offset = 0
    for cell in value.cells:
        count = len(cell.perimeter_samples)
        assignments.append(CellClusterAssignment(cell.id, tuple(sorted(set(raw.labels[offset:offset + count])))))
        offset += count
    return ClusteringResult(clusters, points, raw.labels, tuple(assignments), raw.iterations, raw.converged, tolerance, clusterer.profile.value, raw.random_seed)


__all__ = ["CellClusterAssignment", "Cluster", "ClusteringResult", "cluster_map", "lloyd_cluster"]
