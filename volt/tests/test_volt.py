from __future__ import annotations
import pytest
from volt.models.tool import Tool, ExecutionRecord
from volt.core.search import search_tools
from volt.core.tool_manager import (
    load_catalog,
    detect_all,
    get_categories,
    get_category_counts,
    get_tools_by_category,
)


@pytest.fixture
def sample_tools():
    return [
        Tool(
            name="TestTool1",
            description="Test tool for testing",
            category="Reconnaissance",
            command="test1",
            tags=["test", "recon"],
        ),
        Tool(
            name="TestTool2",
            description="Another test tool",
            category="Web Security",
            command="test2",
            tags=["test", "web"],
        ),
        Tool(
            name="NetworkScanner",
            description="Network scanning tool",
            category="Network",
            command="netscan",
            tags=["network", "scan"],
        ),
    ]


def test_tool_creation():
    tool = Tool(
        name="Nmap",
        description="Network scanner",
        category="Reconnaissance",
        command="nmap",
    )
    assert tool.name == "Nmap"
    assert tool.installed is False


def test_tool_to_dict():
    tool = Tool(
        name="Nmap",
        description="Network scanner",
        category="Reconnaissance",
        command="nmap",
        tags=["network"],
    )
    d = tool.to_dict()
    assert d["name"] == "Nmap"
    assert d["tags"] == ["network"]


def test_tool_from_dict():
    data = {
        "name": "Nmap",
        "description": "Network scanner",
        "category": "Reconnaissance",
        "command": "nmap",
        "tags": ["network"],
    }
    tool = Tool.from_dict(data)
    assert tool.name == "Nmap"


def test_search_by_name(sample_tools):
    results = search_tools(sample_tools, "Nmap")
    assert len(results) == 0


def test_search_by_tag(sample_tools):
    results = search_tools(sample_tools, "recon")
    assert len(results) == 1
    assert results[0].name == "TestTool1"


def test_search_by_category(sample_tools):
    results = search_tools(sample_tools, "network")
    assert len(results) == 1
    assert results[0].name == "NetworkScanner"


def test_search_case_insensitive(sample_tools):
    results = search_tools(sample_tools, "TEST")
    assert len(results) == 2


def test_search_empty_query(sample_tools):
    results = search_tools(sample_tools, "")
    assert len(results) == 3


def test_load_catalog():
    tools = load_catalog()
    assert len(tools) > 0
    assert all(isinstance(t, Tool) for t in tools)


def test_get_categories(sample_tools):
    cats = get_categories(sample_tools)
    assert len(cats) == 3
    assert "Reconnaissance" in cats


def test_get_category_counts(sample_tools):
    counts = get_category_counts(sample_tools)
    assert counts["Reconnaissance"] == 1
    assert counts["Web Security"] == 1


def test_get_tools_by_category(sample_tools):
    tools = get_tools_by_category(sample_tools, "Reconnaissance")
    assert len(tools) == 1
    assert tools[0].name == "TestTool1"


def test_execution_record():
    record = ExecutionRecord(
        tool_name="Nmap",
        command="nmap -sV",
        timestamp="2026-08-26 20:00:00",
        exit_code=0,
        duration=1.5,
    )
    assert record.tool_name == "Nmap"
    assert record.exit_code == 0
