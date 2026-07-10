"""Standalone path-allocation UI renderer."""

from __future__ import annotations

import json
from importlib.resources import files


def render_path_ui(data: dict[str, object]) -> str:
    root = files(__package__)
    template = root.joinpath("path_ui.html").read_text(encoding="utf-8")
    style = root.joinpath("path_ui.css").read_text(encoding="utf-8")
    script = root.joinpath("path_ui.js").read_text(encoding="utf-8")
    return template.replace("__STYLE__", style).replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__SCRIPT__", script)


def render_progress_ui(data: dict[str, object]) -> str:
    root = files(__package__)
    template = root.joinpath("progress_ui.html").read_text(encoding="utf-8")
    style = root.joinpath("progress_ui.css").read_text(encoding="utf-8")
    script = root.joinpath("progress_ui.js").read_text(encoding="utf-8")
    return template.replace("__STYLE__", style).replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__SCRIPT__", script)


def render_path_comparison_ui(data: dict[str, object]) -> str:
    root = files(__package__)
    template = root.joinpath("path_comparison_ui.html").read_text(encoding="utf-8")
    style = root.joinpath("path_comparison_ui.css").read_text(encoding="utf-8")
    script = root.joinpath("path_comparison_ui.js").read_text(encoding="utf-8")
    return template.replace("__STYLE__", style).replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__SCRIPT__", script)


__all__ = ["render_path_comparison_ui", "render_path_ui", "render_progress_ui"]
