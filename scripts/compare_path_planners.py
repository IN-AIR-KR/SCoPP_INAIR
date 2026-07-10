"""Compare current metric-TSP and public-code NN orders on executable KPI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statistics import fmean

from scopp.map.io import load_map
from scopp.path_comparison import compare_path_planners


def _improvement(current: float, baseline: float) -> float:
    return 100.0 * (baseline - current) / baseline if baseline else 0.0


def _max_mean_ratio(values: list[float]) -> float:
    mean = fmean(values) if values else 0.0
    return (max(values) / mean) if mean else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("map_file", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--bias", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=Path("artifacts/path_planner_exec_only_v1.json"))
    parser.add_argument("--plot", type=Path, default=Path("artifacts/path_planner_exec_only_v1.png"))
    args = parser.parse_args()

    report = compare_path_planners(load_map(args.map_file), random_seed=args.seed, auction_bias=args.bias)
    current, public = report.current_metric_tsp, report.public_code_nn

    data = report.to_dict()
    data["improvement_percent"] = {
        "executable_makespan": _improvement(current.executable_makespan_m, public.executable_makespan_m),
        "executable_total": _improvement(current.executable_total_m, public.executable_total_m),
    }
    data["interpretation"] = {
        "executable": "Both visit orders expanded through the local valid-cell 4-neighbour grid-adjacent model.",
        "public_code_reference": "adamslab-ub/SCoPP main efa53a07013fe5fb7c875bfe9b21a22c0980ad6e",
        "runtime_warning": "One-shot ordering plus route expansion time; use only as a diagnostic.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    labels = [node.node_id for node in current.nodes]
    x = range(len(labels))
    width = 0.36
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    colors = ("#2563eb", "#f97316")

    axes[0, 0].bar([i - width / 2 for i in x], [n.executable_distance_m for n in current.nodes], width, label="Metric-TSP", color=colors[0])
    axes[0, 0].bar([i + width / 2 for i in x], [n.executable_distance_m for n in public.nodes], width, label="public-code NN", color=colors[1])
    axes[0, 0].set(title="Executable distance by node", ylabel="distance (m)", xticks=list(x), xticklabels=labels)
    axes[0, 0].legend()

    team_labels = ["Makespan", "Total distance"]
    current_team = [current.executable_makespan_m, current.executable_total_m]
    public_team = [public.executable_makespan_m, public.executable_total_m]
    axes[0, 1].bar([i - width / 2 for i in range(2)], current_team, width, color=colors[0])
    axes[0, 1].bar([i + width / 2 for i in range(2)], public_team, width, color=colors[1])
    axes[0, 1].set(title="Team-level executable KPI", ylabel="distance (m)", xticks=range(2), xticklabels=team_labels)

    node_improvement = [_improvement(cur.executable_distance_m, pub.executable_distance_m) for cur, pub in zip(current.nodes, public.nodes)]
    axes[1, 0].bar(list(x), node_improvement, width=0.6, color="#22c55e")
    axes[1, 0].axhline(0.0, color="#475569", linewidth=1)
    axes[1, 0].set(title="Node improvement vs NN", ylabel="improvement (%)", xticks=list(x), xticklabels=labels)

    balance_labels = ["CV", "Max/mean"]
    axes[1, 1].bar(
        [i - width / 2 for i in range(2)],
        [current.executable_distance_cv, _max_mean_ratio([node.executable_distance_m for node in current.nodes])],
        width,
        color=colors[0],
    )
    axes[1, 1].bar(
        [i + width / 2 for i in range(2)],
        [public.executable_distance_cv, _max_mean_ratio([node.executable_distance_m for node in public.nodes])],
        width,
        color=colors[1],
    )
    axes[1, 1].set(title="Executable balance", ylabel="ratio (lower is better)", xticks=range(2), xticklabels=balance_labels)

    for axis in axes.flat:
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle(
        f"Fixed official_minibatch allocation - executable path-planner comparison\n"
        f"{report.map_name} (arbitrary indoor map; not a paper experimental site), seed={report.random_seed}"
    )
    fig.tight_layout()
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.plot, dpi=180, bbox_inches="tight")
    print(f"wrote {args.output} and {args.plot}")


if __name__ == "__main__":
    main()
