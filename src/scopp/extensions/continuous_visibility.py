"""Continuous collision-free transit as an explicit non-paper extension.

The SCoPP paper and public implementation connect coverage targets by
Euclidean nearest-neighbour segments.  This module instead keeps an existing
cell visit order fixed and expands it through the continuous free space using
a deterministic polygon visibility graph.  AOI boundaries may be followed;
no-fly zones are buffered by ``clearance_m`` before routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot, isfinite

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from scopp.algorithm.path_planning import NodePath, PathPlan
from scopp.map.geometry import polygon_from_spec, valid_polygonal
from scopp.map.models import DiscretizedMap, XY


class ContinuousTransitError(ValueError):
    """Base error for the safety-constrained transit extension."""


class PointOutsideFreeSpaceError(ContinuousTransitError):
    """Raised when a start or target is outside the clearance-adjusted AOI."""


class NoContinuousPathError(ContinuousTransitError):
    """Raised when no collision-free continuous path connects two points."""


class TargetNotFlyableError(ContinuousTransitError):
    """Raised when a cell has no coverage target inside continuous free space."""


@dataclass(frozen=True, slots=True)
class ContinuousNodePath:
    node_id: str
    cell_ids: tuple[str, ...]
    coverage_targets: tuple[XY, ...]
    trajectory: tuple[XY, ...]
    return_waypoint_index: int
    distance_m: float
    clearance_m: float


@dataclass(frozen=True, slots=True)
class ContinuousPathPlan:
    paths: tuple[ContinuousNodePath, ...]

    @property
    def makespan_distance_m(self) -> float:
        return max((path.distance_m for path in self.paths), default=0.0)

    @property
    def total_distance_m(self) -> float:
        return sum(path.distance_m for path in self.paths)


def _free_space(mapped: DiscretizedMap, clearance_m: float):
    if not isfinite(clearance_m) or clearance_m < 0:
        raise ValueError("clearance_m must be finite and non-negative")
    aoi = polygon_from_spec(mapped.source.aoi)
    obstacles = unary_union(tuple(polygon_from_spec(zone) for zone in mapped.source.no_fly_zones))
    # AOI is an operational containment boundary, not a physical obstacle: its
    # boundary may be followed.  Clearance applies to no-fly safety obstacles.
    free = aoi
    if not obstacles.is_empty:
        blocked = obstacles.buffer(clearance_m, join_style="mitre") if clearance_m else obstacles
        free = free.difference(blocked)
    return valid_polygonal(free)


def _component_for_point(free_space, point: XY) -> Polygon:
    candidate = Point(point)
    components = (free_space,) if isinstance(free_space, Polygon) else tuple(free_space.geoms) if isinstance(free_space, MultiPolygon) else ()
    for component in components:
        if component.covers(candidate):
            return component
    raise PointOutsideFreeSpaceError(f"point {point!r} is outside the clearance-adjusted free space")


def _ring_vertices(component: Polygon) -> tuple[XY, ...]:
    vertices = [(float(x), float(y)) for x, y in component.exterior.coords[:-1]]
    for ring in component.interiors:
        vertices.extend((float(x), float(y)) for x, y in ring.coords[:-1])
    return tuple(sorted(set(vertices)))


def shortest_visibility_path(free_space, start: XY, goal: XY) -> tuple[XY, ...]:
    """Return a deterministic shortest polyline within one free-space polygon."""
    component = _component_for_point(free_space, start)
    if not component.covers(Point(goal)):
        raise NoContinuousPathError(f"goal {goal!r} is not in the start point's free-space component")
    if start == goal:
        return (start,)
    direct = LineString((start, goal))
    if component.covers(direct):
        return (start, goal)

    vertices = (start, goal) + tuple(vertex for vertex in _ring_vertices(component) if vertex not in (start, goal))
    graph: list[list[tuple[int, float]]] = [[] for _ in vertices]
    for left in range(len(vertices)):
        for right in range(left + 1, len(vertices)):
            segment = LineString((vertices[left], vertices[right]))
            if component.covers(segment):
                weight = hypot(vertices[right][0] - vertices[left][0], vertices[right][1] - vertices[left][1])
                graph[left].append((right, weight))
                graph[right].append((left, weight))
    for edges in graph:
        edges.sort(key=lambda item: vertices[item[0]])

    best: dict[int, tuple[float, tuple[int, ...]]] = {0: (0.0, (0,))}
    queue: list[tuple[float, tuple[int, ...], int]] = [(0.0, (0,), 0)]
    while queue:
        distance, path, node = heappop(queue)
        if best.get(node) != (distance, path):
            continue
        if node == 1:
            return tuple(vertices[index] for index in path)
        for neighbor, weight in graph[node]:
            candidate = (distance + weight, path + (neighbor,))
            incumbent = best.get(neighbor)
            if incumbent is None or candidate < incumbent:
                best[neighbor] = candidate
                heappush(queue, (candidate[0], candidate[1], neighbor))
    raise NoContinuousPathError(f"no continuous path between {start!r} and {goal!r}")


def _expand_node(mapped: DiscretizedMap, source: NodePath, clearance_m: float) -> ContinuousNodePath:
    free = _free_space(mapped, clearance_m)
    _component_for_point(free, source.start)
    cells = {cell.id: cell for cell in mapped.cells}
    targets: list[XY] = []
    for cell_id, center in zip(source.cell_ids, source.waypoints):
        if free.covers(Point(center)):
            target = center
        else:
            coverage = unary_union(tuple(polygon_from_spec(spec) for spec in cells[cell_id].coverage_geometry))
            reachable_coverage = valid_polygonal(coverage.intersection(free))
            if reachable_coverage.is_empty:
                raise TargetNotFlyableError(f"coverage cell {cell_id!r} has no target inside continuous free space")
            representative = reachable_coverage.representative_point()
            target = (float(representative.x), float(representative.y))
        component = _component_for_point(free, target)
        if not component.covers(Point(source.start)):
            raise NoContinuousPathError(f"coverage target {cell_id!r} is disconnected from node {source.node_id!r}")
        targets.append(target)

    trajectory: list[XY] = [source.start]
    current = source.start
    for target in targets:
        segment = shortest_visibility_path(free, current, target)
        trajectory.extend(segment[1:])
        current = target
    return_index = len(trajectory) - 1
    if targets:
        trajectory.extend(shortest_visibility_path(free, current, source.start)[1:])
    distance = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(trajectory, trajectory[1:]))
    return ContinuousNodePath(source.node_id, source.cell_ids, tuple(targets), tuple(trajectory), return_index, distance, clearance_m)


def expand_plan_continuous(mapped: DiscretizedMap, source: PathPlan, *, clearance_m: float = 0.1) -> ContinuousPathPlan:
    """Expand fixed visit orders into continuous AOI/no-fly-safe trajectories."""
    return ContinuousPathPlan(tuple(_expand_node(mapped, path, clearance_m) for path in source.paths))
