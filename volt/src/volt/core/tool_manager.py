from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from volt.models.tool import Tool

_CATALOG_PATH: Optional[Path] = None


def _find_catalog() -> Path:
    global _CATALOG_PATH
    if _CATALOG_PATH:
        return _CATALOG_PATH

    candidates = [
        Path(__file__).parent.parent.parent.parent.parent / "data" / "tools.json",
        Path(__file__).parent.parent.parent.parent / "data" / "tools.json",
        Path.home() / ".local" / "share" / "volt" / "tools.json",
    ]

    for p in candidates:
        if p.exists():
            _CATALOG_PATH = p
            return p

    raise FileNotFoundError("Tool catalog not found")


def load_catalog() -> list[Tool]:
    catalog_path = _find_catalog()
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Tool.from_dict(item) for item in data]


def detect_installed(tool: Tool) -> Tool:
    binary = tool.binary or tool.command
    binary_path = shutil.which(binary)
    if binary_path:
        tool.installed = True
        tool.binary_path = binary_path
    else:
        tool.installed = False
        tool.binary_path = ""
    return tool


def detect_all(tools: list[Tool]) -> list[Tool]:
    return [detect_installed(t) for t in tools]


def get_tool_by_name(tools: list[Tool], name: str) -> Optional[Tool]:
    for tool in tools:
        if tool.name.lower() == name.lower():
            return tool
    return None


def get_tools_by_category(tools: list[Tool], category: str) -> list[Tool]:
    return [t for t in tools if t.category.lower() == category.lower()]


def get_categories(tools: list[Tool]) -> list[str]:
    categories = sorted(set(t.category for t in tools))
    return categories


def get_category_counts(tools: list[Tool]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in tools:
        counts[t.category] = counts.get(t.category, 0) + 1
    return counts
