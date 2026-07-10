"""Build a standalone executable KPI comparison UI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scopp.algorithm.path_planning import plan_coverage_paths
from scopp.config import ClusteringProfile, PathPlanningProfile, ScoppConfig
from scopp.pipeline import ScoppPipeline
from scopp.ui import render_path_comparison_ui


def _node_start_map(base) -> dict[str, tuple[float, float]]:
    return {node.id: node.position for node in base.mapped.source.node_starts}


def _allocation_size_map(base) -> dict[str, int]:
    return {node.node_id: len(node.cell_ids) for node in base.allocation.nodes}


def _path_map(plan) -> dict[str, object]:
    return {path.node_id: path for path in plan.paths}


def build_data(map_file: Path, *, seed: int, bias: float) -> dict[str, object]:
    base = ScoppPipeline(
        ScoppConfig(
            clustering_profile=ClusteringProfile.OFFICIAL_MINIBATCH,
            random_seed=seed,
            auction_bias=bias,
        )
    ).run_map(map_file)
    metric_plan = plan_coverage_paths(base.mapped, base.allocation, profile=PathPlanningProfile.METRIC_TSP)
    nn_plan = plan_coverage_paths(base.mapped, base.allocation, profile=PathPlanningProfile.PAPER_NN)
    metric_by_id = _path_map(metric_plan)
    nn_by_id = _path_map(nn_plan)
    start_by_id = _node_start_map(base)
    allocation_size_by_id = _allocation_size_map(base)

    return {
        "name": base.mapped.source.name,
        "seed": seed,
        "bias": bias,
        "cellWidth": base.mapped.cell_width_m,
        "aoi": base.mapped.source.aoi.exterior,
        "noFly": [zone.exterior for zone in base.mapped.source.no_fly_zones],
        "cells": [{"id": cell.id, "vertices": cell.vertices} for cell in base.mapped.cells],
        "nodes": [
            {
                "id": node.id,
                "start": start_by_id[node.id],
                "cells": allocation_size_by_id[node.id],
                "cellIds": metric_by_id[node.id].cell_ids,
                "metric": {
                    "trajectory": metric_by_id[node.id].trajectory,
                    "distance": metric_by_id[node.id].distance_m,
                },
                "nn": {
                    "trajectory": nn_by_id[node.id].trajectory,
                    "distance": nn_by_id[node.id].distance_m,
                },
            }
            for node in base.mapped.source.node_starts
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("map_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/path_comparison_ui.html"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--bias", type=float, default=0.5)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    html = render_path_comparison_ui(build_data(args.map_file, seed=args.seed, bias=args.bias))
    args.output.write_text(html, encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
