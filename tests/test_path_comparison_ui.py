from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_path_comparison_ui_builds_standalone_html(tmp_path: Path) -> None:
    output = tmp_path / "comparison.html"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_path_comparison_ui.py"),
            str(ROOT / "examples/maps/indoor_lab.yaml"),
            "--output",
            str(output),
            "--seed",
            "0",
            "--bias",
            "0.5",
        ],
        check=True,
    )
    html = output.read_text(encoding="utf-8")
    assert "Metric-TSP vs public-code NN" in html
    assert 'data-testid="node-select"' in html
    assert "__DATA__" not in html
