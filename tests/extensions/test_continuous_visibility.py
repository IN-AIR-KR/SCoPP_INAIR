from math import hypot

import pytest
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from scopp.config import ClusteringProfile, ScoppConfig
from scopp.extensions.continuous_visibility import NoContinuousPathError, expand_plan_continuous, shortest_visibility_path
from scopp.map.geometry import polygon_from_spec
from scopp.pipeline import ScoppPipeline


def _length(path):
    return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))


def test_visibility_path_is_diagonal_when_direct_segment_is_safe() -> None:
    free = Polygon(((0, 0), (5, 0), (5, 5), (0, 5)))
    path = shortest_visibility_path(free, (1, 1), (4, 4))
    assert path == ((1, 1), (4, 4))
    assert _length(path) == pytest.approx(3 * 2**0.5)


def test_visibility_path_routes_around_no_fly_hole() -> None:
    free = Polygon(((0, 0), (6, 0), (6, 6), (0, 6)), holes=(((2, 2), (4, 2), (4, 4), (2, 4)),))
    path = shortest_visibility_path(free, (1, 3), (5, 3))
    route = LineString(path)
    obstacle_interior = Polygon(((2, 2), (4, 2), (4, 4), (2, 4))).buffer(-1e-9)
    assert len(path) > 2
    assert route.intersection(obstacle_interior).is_empty
    assert free.covers(route)
    assert _length(path) > 4.0


def test_visibility_path_rejects_disconnected_goal() -> None:
    free = Polygon(((0, 0), (2, 0), (2, 2), (0, 2))).union(Polygon(((4, 0), (6, 0), (6, 2), (4, 2))))
    with pytest.raises(NoContinuousPathError):
        shortest_visibility_path(free, (1, 1), (5, 1))


def test_indoor_routes_remain_inside_aoi_and_clear_no_fly_zones() -> None:
    result = ScoppPipeline(ScoppConfig(clustering_profile=ClusteringProfile.OFFICIAL_MINIBATCH, random_seed=0)).run_map("examples/maps/indoor_lab.yaml")
    continuous = expand_plan_continuous(result.mapped, result.plan, clearance_m=0.1)
    aoi = polygon_from_spec(result.mapped.source.aoi)
    blocked = unary_union(tuple(polygon_from_spec(zone).buffer(0.1, join_style="mitre") for zone in result.mapped.source.no_fly_zones))

    for path in continuous.paths:
        assert path.trajectory[0] == path.trajectory[-1]
        for start, end in zip(path.trajectory, path.trajectory[1:]):
            segment = LineString((start, end))
            assert aoi.covers(segment)
            assert blocked.buffer(-1e-9).intersection(segment).is_empty
