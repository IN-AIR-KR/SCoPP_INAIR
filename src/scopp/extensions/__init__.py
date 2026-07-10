"""Explicit non-paper extensions for execution-constrained planning."""

from .continuous_visibility import (
    ContinuousNodePath,
    ContinuousPathPlan,
    NoContinuousPathError,
    PointOutsideFreeSpaceError,
    TargetNotFlyableError,
    expand_plan_continuous,
    shortest_visibility_path,
)

__all__ = [
    "ContinuousNodePath",
    "ContinuousPathPlan",
    "NoContinuousPathError",
    "PointOutsideFreeSpaceError",
    "TargetNotFlyableError",
    "expand_plan_continuous",
    "shortest_visibility_path",
]
