from __future__ import annotations
from typing import Optional

from volt.models.tool import Tool


def search_tools(tools: list[Tool], query: str) -> list[Tool]:
    if not query:
        return tools

    query_lower = query.lower()
    results = []
    for tool in tools:
        if (
            query_lower in tool.name.lower()
            or query_lower in tool.description.lower()
            or query_lower in tool.category.lower()
            or any(query_lower in tag.lower() for tag in tool.tags)
        ):
            results.append(tool)

    return results
