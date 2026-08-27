from __future__ import annotations
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="volt",
        description="VOLT — Security Toolkit Manager for Kali Linux",
    )
    parser.add_argument(
        "--version", "-v", action="version", version="volt 0.1.0"
    )
    parser.add_argument(
        "--search", "-s", type=str, help="Search for a tool"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all tools"
    )
    parser.add_argument(
        "--category", "-c", type=str, help="List tools in a category"
    )
    parser.add_argument(
        "--tui", action="store_true", help="Launch the TUI (default)"
    )

    args = parser.parse_args()

    if args.search:
        _search(args.search)
    elif args.list:
        _list_all()
    elif args.category:
        _list_category(args.category)
    else:
        _launch_tui()


def _search(query: str):
    from volt.core.tool_manager import load_catalog, detect_all
    from volt.core.search import search_tools

    tools = detect_all(load_catalog())
    results = search_tools(tools, query)

    if not results:
        print(f"No tools found matching '{query}'")
        return

    print(f"\nResults for '{query}':\n")
    for tool in results:
        status = "INSTALLED" if tool.installed else "NOT INSTALLED"
        print(f"  {tool.name}")
        print(f"    {tool.description}")
        print(f"    Status: {status}")
        if tool.binary_path:
            print(f"    Binary: {tool.binary_path}")
        print()


def _list_all():
    from volt.core.tool_manager import load_catalog, detect_all

    tools = detect_all(load_catalog())
    print(f"\nAll Tools ({len(tools)}):\n")
    for tool in tools:
        status = "[OK]" if tool.installed else "[--]"
        print(f"  {status}  {tool.name:<20} {tool.description[:40]}")
    print()


def _list_category(category: str):
    from volt.core.tool_manager import load_catalog, detect_all, get_tools_by_category

    tools = detect_all(load_catalog())
    cat_tools = get_tools_by_category(tools, category)

    if not cat_tools:
        print(f"No tools found in category '{category}'")
        return

    print(f"\n{category} ({len(cat_tools)}):\n")
    for tool in cat_tools:
        status = "[OK]" if tool.installed else "[--]"
        print(f"  {status}  {tool.name:<20} {tool.description[:40]}")
    print()


def _launch_tui():
    from volt.app import VoltApp

    app = VoltApp()
    app.run()


if __name__ == "__main__":
    main()
