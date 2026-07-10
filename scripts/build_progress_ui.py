"""Build a standalone project-progress dashboard."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scopp import ClusteringProfile, ScoppConfig, ScoppPipeline
from scopp.ui import render_progress_ui


def _test_count() -> int:
    env = {**os.environ, "LOKY_MAX_CPU_COUNT": "4"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=True,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    return int(match.group(1)) if match else 0


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, default=ROOT / "examples/maps/indoor_lab.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/progress_ui.html")
    args = parser.parse_args()

    runs = []
    for profile in ClusteringProfile:
        result = ScoppPipeline(ScoppConfig(profile, random_seed=0)).run_map(args.map)
        runs.append(
            {
                "name": profile.value,
                "cells": [len(path.cell_ids) for path in result.plan.paths],
                "makespan": result.plan.makespan_distance_m,
            }
        )

    data = {
        "commit": _commit(),
        "tests": _test_count(),
        "pythonFiles": len(tuple(ROOT.glob("src/**/*.py"))) + len(tuple(ROOT.glob("scripts/*.py"))),
        "cellCount": len(ScoppPipeline().run_map(args.map).mapped.cells),
        "profiles": runs,
        "stages": [
            {"name": "맵 모델", "detail": "AOI, no-fly, Shapely", "status": "done"},
            {"name": "격자화", "detail": "FoV 기반 cell 생성", "status": "done"},
            {"name": "Clustering", "detail": "Lloyd / MiniBatch", "status": "done"},
            {"name": "경쟁 해소", "detail": "Conflict cell 탐지", "status": "done"},
            {"name": "CPP", "detail": "Nearest neighbor", "status": "done"},
            {"name": "집계", "detail": "Makespan / 경로 길이", "status": "done"},
            {"name": "UI", "detail": "경로 비교 대시보드 생성", "status": "done"},
        ],
        "links": [
            {"name": "경로 이동 UI", "href": "path_ui.html"},
            {"name": "실행 기준 비교 UI", "href": "path_comparison_ui.html"},
            {"name": "실행 KPI 그래프", "href": "path_planner_exec_only_v1.png"},
            {"name": "KPI 요약 문서", "href": "executable_kpi_result.md"},
            {"name": "README", "href": "../README.md"},
        ],
        "next": [
            {
                "name": "경로 성능",
                "detail": "동적 장애가 없는 KD-tree 기반 탐색과 grid-adjacent executable 비교를 더 확장할 수 있습니다.",
            },
            {
                "name": "실내 비행",
                "detail": "Cell 인접 이동과 no-fly 차단을 유지한 상태에서 추가 제약을 실험할 수 있습니다.",
            },
            {
                "name": "검증 강화",
                "detail": "Seed 고정 재현성과 KPI 계산 일치성을 추가로 점검할 수 있습니다.",
            },
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_progress_ui(data), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
