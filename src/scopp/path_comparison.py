"""Fair path-planner comparison on one fixed SCoPP allocation.

The public-code baseline is the closed Euclidean greedy nearest-neighbor tour:
robot start -> assigned cell centres -> robot start.  Executable distances are
reported separately because the indoor implementation expands an order over
the valid-cell graph with four-neighbour A* transit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import hypot
from statistics import fmean, pstdev
from time import perf_counter

from scopp.algorithm.path_planning import NodePath, PathPlan, plan_coverage_paths
from scopp.config import ClusteringProfile, PathPlanningProfile, ScoppConfig
from scopp.map.models import MapDefinition
from scopp.pipeline import ScoppPipeline


def _closed_euclidean_distance(path: NodePath) -> float:
    points = (path.start,) + path.waypoints + ((path.start,) if path.waypoints else ())
    return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def _cv(values: tuple[float, ...]) -> float:
    mean = fmean(values) if values else 0.0
    return pstdev(values) / mean if mean else 0.0


@dataclass(frozen=True, slots=True)
class PlannerNodeComparison:
    node_id: str
    cell_count: int
    direct_distance_m: float
    executable_distance_m: float
    transit_inflation: float


@dataclass(frozen=True, slots=True)
class PlannerComparison:
    planner: str
    nodes: tuple[PlannerNodeComparison, ...]
    direct_makespan_m: float
    direct_total_m: float
    direct_distance_cv: float
    direct_max_mean_ratio: float
    executable_makespan_m: float
    executable_total_m: float
    executable_distance_cv: float
    planning_runtime_s: float


@dataclass(frozen=True, slots=True)
class PathComparisonReport:
    schema_version: str
    map_name: str
    clustering_profile: str
    random_seed: int
    auction_bias: float
    cell_count: int
    conflict_cell_count: int
    assignment: tuple[tuple[str, int], ...]
    current_metric_tsp: PlannerComparison
    public_code_nn: PlannerComparison

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _summarize(name: str, plan: PathPlan, runtime_s: float) -> PlannerComparison:
    direct = tuple(_closed_euclidean_distance(path) for path in plan.paths)
    executable = tuple(path.distance_m for path in plan.paths)
    nodes = tuple(
        PlannerNodeComparison(
            path.node_id,
            len(path.cell_ids),
            direct_distance,
            executable_distance,
            executable_distance / direct_distance if direct_distance else 1.0,
        )
        for path, direct_distance, executable_distance in zip(plan.paths, direct, executable)
    )
    direct_mean = fmean(direct) if direct else 0.0
    return PlannerComparison(
        name,
        nodes,
        max(direct, default=0.0),
        sum(direct),
        _cv(direct),
        max(direct, default=0.0) / direct_mean if direct_mean else 0.0,
        plan.makespan_distance_m,
        plan.total_distance_m,
        _cv(executable),
        runtime_s,
    )


def compare_path_planners(
    definition: MapDefinition,
    *,
    random_seed: int = 0,
    auction_bias: float = 0.5,
) -> PathComparisonReport:
    """Compare both orders using exactly one MiniBatch clustering/allocation."""
    base = ScoppPipeline(
        ScoppConfig(
            clustering_profile=ClusteringProfile.OFFICIAL_MINIBATCH,
            path_planning_profile=PathPlanningProfile.PAPER_NN,
            random_seed=random_seed,
            auction_bias=auction_bias,
        )
    ).run_definition(definition)

    start = perf_counter()
    metric_plan = plan_coverage_paths(base.mapped, base.allocation, profile=PathPlanningProfile.METRIC_TSP)
    metric_runtime = perf_counter() - start
    start = perf_counter()
    nn_plan = plan_coverage_paths(base.mapped, base.allocation, profile=PathPlanningProfile.PAPER_NN)
    nn_runtime = perf_counter() - start

    return PathComparisonReport(
        "1.0",
        definition.name,
        ClusteringProfile.OFFICIAL_MINIBATCH.value,
        random_seed,
        auction_bias,
        len(base.mapped.cells),
        len(base.allocation.auction_decisions),
        tuple((node.node_id, len(node.cell_ids)) for node in base.allocation.nodes),
        _summarize("current_metric_tsp", metric_plan, metric_runtime),
        _summarize("public_code_nn", nn_plan, nn_runtime),
    )


__all__ = ["PathComparisonReport", "compare_path_planners"]
