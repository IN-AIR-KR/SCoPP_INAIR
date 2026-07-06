"""Nearest-neighbor coverage paths from SCoPP Section III-E."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import hypot

from scopp.algorithm.auction import AllocationResult
from scopp.map.models import DiscretizedMap, XY


@dataclass(frozen=True, slots=True)
class _PointItem:
    point: XY
    stable_index: int
    cell_id: str


@dataclass(frozen=True, slots=True)
class _KDNode:
    item: _PointItem
    axis: int
    left: _KDNode | None
    right: _KDNode | None


def _build(items: tuple[_PointItem, ...], depth: int = 0) -> _KDNode | None:
    if not items:
        return None
    axis = depth % 2
    ordered = tuple(sorted(items, key=lambda item: (item.point[axis], item.point[1 - axis], item.stable_index)))
    middle = len(ordered) // 2
    return _KDNode(ordered[middle], axis, _build(ordered[:middle], depth + 1), _build(ordered[middle + 1 :], depth + 1))


def _nearest(root: _KDNode, target: XY) -> _PointItem:
    best_item = root.item
    best_key = ((root.item.point[0] - target[0]) ** 2 + (root.item.point[1] - target[1]) ** 2, root.item.stable_index)

    def visit(node: _KDNode | None) -> None:
        nonlocal best_item, best_key
        if node is None:
            return
        distance = (node.item.point[0] - target[0]) ** 2 + (node.item.point[1] - target[1]) ** 2
        key = (distance, node.item.stable_index)
        if key < best_key:
            best_item, best_key = node.item, key
        delta = target[node.axis] - node.item.point[node.axis]
        near, far = (node.left, node.right) if delta <= 0 else (node.right, node.left)
        visit(near)
        if delta * delta <= best_key[0]:
            visit(far)

    visit(root)
    return best_item


@dataclass(frozen=True, slots=True)
class NodePath:
    cluster_index: int
    node_id: str
    start: XY
    cell_ids: tuple[str, ...]
    waypoints: tuple[XY, ...]
    motion_cell_ids: tuple[str, ...]
    motion_waypoints: tuple[XY, ...]
    return_motion_index: int
    distance_m: float

    @property
    def trajectory(self) -> tuple[XY, ...]:
        """Official-code trajectory: start, all cell centres, then return."""
        return (self.start,) + self.motion_waypoints + ((self.start,) if self.motion_waypoints else ())


@dataclass(frozen=True, slots=True)
class PathPlan:
    paths: tuple[NodePath, ...]

    @property
    def makespan_distance_m(self) -> float:
        """Return the longest node path, the paper objective at equal speed."""
        return max((path.distance_m for path in self.paths), default=0.0)

    @property
    def total_distance_m(self) -> float:
        return sum(path.distance_m for path in self.paths)


def _ordered_nearest_neighbor(start: XY, items: tuple[_PointItem, ...]) -> tuple[_PointItem, ...]:
    remaining = items
    current = start
    route: list[_PointItem] = []
    while remaining:
        tree = _build(remaining)
        assert tree is not None
        chosen = _nearest(tree, current)
        route.append(chosen)
        current = chosen.point
        remaining = tuple(item for item in remaining if item.cell_id != chosen.cell_id)
    return tuple(route)


class NoAdjacentPathError(ValueError):
    """Raised when two coverage targets cannot be connected by valid cells."""


def _adjacent_path(start_id: str, goal_id: str, cells_by_id, ids_by_key) -> tuple[str, ...]:
    """Return a deterministic 4-neighbor A* path including both endpoints."""
    if start_id == goal_id:
        return (start_id,)
    start, goal = cells_by_id[start_id], cells_by_id[goal_id]
    start_key, goal_key = (start.row, start.col), (goal.row, goal.col)
    frontier: list[tuple[int, int, int, tuple[int, int]]] = []
    heappush(frontier, (0, 0, 0, start_key))
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start_key: None}
    cost = {start_key: 0}
    sequence = 0
    neighbor_offsets = ((-1, 0), (0, -1), (0, 1), (1, 0))
    while frontier:
        _, current_cost, _, current = heappop(frontier)
        if current == goal_key:
            keys: list[tuple[int, int]] = []
            cursor: tuple[int, int] | None = current
            while cursor is not None:
                keys.append(cursor)
                cursor = came_from[cursor]
            return tuple(ids_by_key[key] for key in reversed(keys))
        if current_cost != cost[current]:
            continue
        for dr, dc in neighbor_offsets:
            neighbor = (current[0] + dr, current[1] + dc)
            if neighbor not in ids_by_key:
                continue
            new_cost = current_cost + 1
            if new_cost < cost.get(neighbor, 10**18):
                cost[neighbor] = new_cost
                came_from[neighbor] = current
                sequence += 1
                heuristic = abs(neighbor[0] - goal_key[0]) + abs(neighbor[1] - goal_key[1])
                heappush(frontier, (new_cost + heuristic, new_cost, sequence, neighbor))
    raise NoAdjacentPathError(f"no valid 4-neighbor path between {start_id!r} and {goal_id!r}")


def plan_coverage_paths(mapped: DiscretizedMap, allocation: AllocationResult) -> PathPlan:
    """Order each node's assigned cell centres using KD-tree nearest neighbor."""
    if len(allocation.nodes) != len(mapped.source.node_starts):
        raise ValueError("allocation node count does not match map node count")
    cell_by_id = {cell.id: cell for cell in mapped.cells}
    id_by_key = {(cell.row, cell.col): cell.id for cell in mapped.cells}
    stable_index = {cell.id: index for index, cell in enumerate(mapped.cells)}
    paths: list[NodePath] = []
    node_by_id = {node.id: node for node in mapped.source.node_starts}
    for allocated in allocation.nodes:
        try:
            node = node_by_id[allocated.node_id]
        except KeyError as exc:
            raise ValueError(f"allocation contains unknown node {allocated.node_id!r}") from exc
        items = tuple(_PointItem(cell_by_id[cell_id].center, stable_index[cell_id], cell_id) for cell_id in allocated.cell_ids)
        ordered = _ordered_nearest_neighbor(node.position, items)
        waypoints = tuple(item.point for item in ordered)
        if not ordered:
            paths.append(NodePath(allocated.cluster_index, node.id, node.position, (), (), (), (), 0, 0.0))
            continue
        start_cell = min(mapped.cells, key=lambda cell: ((cell.center[0] - node.position[0]) ** 2 + (cell.center[1] - node.position[1]) ** 2, stable_index[cell.id]))
        motion_ids: list[str] = [start_cell.id]
        current_id = start_cell.id
        for target in ordered:
            segment = _adjacent_path(current_id, target.cell_id, cell_by_id, id_by_key)
            motion_ids.extend(segment[1:])
            current_id = target.cell_id
        return_motion_index = len(motion_ids)
        motion_ids.extend(_adjacent_path(current_id, start_cell.id, cell_by_id, id_by_key)[1:])
        motion_waypoints = tuple(cell_by_id[cell_id].center for cell_id in motion_ids)
        distance = hypot(motion_waypoints[0][0] - node.position[0], motion_waypoints[0][1] - node.position[1])
        distance += sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(motion_waypoints, motion_waypoints[1:]))
        distance += hypot(node.position[0] - motion_waypoints[-1][0], node.position[1] - motion_waypoints[-1][1])
        paths.append(NodePath(allocated.cluster_index, node.id, node.position, tuple(item.cell_id for item in ordered), waypoints, tuple(motion_ids), motion_waypoints, return_motion_index, distance))
    return PathPlan(tuple(paths))


__all__ = ["NoAdjacentPathError", "NodePath", "PathPlan", "plan_coverage_paths"]
