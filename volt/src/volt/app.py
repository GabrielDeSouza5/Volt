from __future__ import annotations
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)

from volt.core.tool_manager import (
    detect_all,
    get_categories,
    get_category_counts,
    load_catalog,
)
from volt.core.search import search_tools
from volt.models.category import CATEGORY_DESCRIPTIONS, CATEGORY_ICONS
from volt.models.tool import Tool
from volt.storage.database import (
    get_favorites,
    get_history,
    get_stats,
    init_db,
    is_favorite,
    toggle_favorite,
)


BANNER = r"""██╗   ██╗ ██████╗ ██╗  ████████╗
██║   ██║██╔═══██╗██║  ╚══██╔══╝
██║   ██║██║   ██║██║     ██║
╚██╗ ██╔╝██║   ██║██║     ██║
 ╚████╔╝ ╚██████╔╝███████╗██║
  ╚═══╝   ╚═════╝ ╚══════╝╚═╝"""


class StatusBar(Static):
    def __init__(self, tools: list[Tool], **kwargs):
        super().__init__(**kwargs)
        self.tools = tools
        self.update_content()

    def update_content(self):
        installed = sum(1 for t in self.tools if t.installed)
        stats = get_stats()
        fav_count = stats["favorites"]
        total = len(self.tools)
        self.update(
            f" Tools: {total}  │  Installed: {installed}  │  Favorites: {fav_count} "
        )


class MainScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "show_favorites", "Favorites"),
        Binding("h", "show_history", "History"),
        Binding("slash", "search", "Search"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "category_by_index(0)"),
        Binding("2", "category_by_index(1)"),
        Binding("3", "category_by_index(2)"),
        Binding("4", "category_by_index(3)"),
        Binding("5", "category_by_index(4)"),
        Binding("6", "category_by_index(5)"),
        Binding("7", "category_by_index(6)"),
        Binding("8", "category_by_index(7)"),
        Binding("9", "category_by_index(8)"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(BANNER, id="banner", classes="center")
        yield Static("Security Toolkit Manager", classes="subtitle center")
        yield Label("")
        yield ListView(id="category_list")
        yield StatusBar(self.app.tools, id="status")
        yield Footer()

    def on_mount(self):
        self._populate_categories()

    def _populate_categories(self):
        lv = self.query_one("#category_list", ListView)
        lv.clear()
        categories = get_categories(self.app.tools)
        counts = get_category_counts(self.app.tools)

        all_item = ListItem(
            Label(f"All Tools  ({len(self.app.tools)})")
        )
        lv.append(all_item)

        for i, cat in enumerate(categories):
            icon = CATEGORY_ICONS.get(cat, "•")
            count = counts.get(cat, 0)
            installed = sum(
                1 for t in self.app.tools if t.category == cat and t.installed
            )
            item = ListItem(
                Label(f"{i+1}. {icon} {cat}  ({installed}/{count})")
            )
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected):
        idx = event.item_index
        if idx == 0:
            self.app.push_screen(ToolListScreen(self.app.tools, "All Tools"))
        else:
            categories = get_categories(self.app.tools)
            if 0 < idx <= len(categories):
                cat = categories[idx - 1]
                cat_tools = [
                    t for t in self.app.tools if t.category == cat
                ]
                self.app.push_screen(
                    ToolListScreen(cat_tools, cat)
                )

    def action_category_by_index(self, index: int):
        categories = get_categories(self.app.tools)
        if index < len(categories):
            cat = categories[index]
            cat_tools = [t for t in self.app.tools if t.category == cat]
            self.app.push_screen(ToolListScreen(cat_tools, cat))

    def action_search(self):
        self.app.push_screen(SearchScreen())

    def action_show_favorites(self):
        self.app.push_screen(FavoritesScreen())

    def action_show_history(self):
        self.app.push_screen(HistoryScreen())

    def action_refresh(self):
        self.app.tools = detect_all(load_catalog())
        self._populate_categories()
        self.query_one("#status", StatusBar).update_content()
        self.notify("Tools refreshed", severity="information")


class ToolListScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("slash", "search", "Search"),
        Binding("enter", "select_tool", "Details"),
        Binding("f", "toggle_fav", "Favorite"),
    ]

    def __init__(self, tools: list[Tool], title: str, **kwargs):
        super().__init__(**kwargs)
        self.tools = tools
        self.screen_title = title

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(f"  {self.screen_title}", id="screen_title")
        yield ListView(id="tool_list")
        yield StatusBar(self.tools, id="status")
        yield Footer()

    def on_mount(self):
        self._populate_tools()

    def _populate_tools(self):
        lv = self.query_one("#tool_list", ListView)
        lv.clear()
        for tool in self.tools:
            status = "✓" if tool.installed else "✗"
            fav = "★" if is_favorite(tool.name) else " "
            label = Label(
                f"  {status}  {fav}  {tool.name}  —  {tool.description[:50]}"
            )
            lv.append(ListItem(label))

    def on_list_view_selected(self, event: ListView.Selected):
        if 0 <= event.item_index < len(self.tools):
            tool = self.tools[event.item_index]
            self.app.push_screen(ToolDetailScreen(tool))

    def action_select_tool(self):
        lv = self.query_one("#tool_list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self.tools):
            tool = self.tools[lv.index]
            self.app.push_screen(ToolDetailScreen(tool))

    def action_toggle_fav(self):
        lv = self.query_one("#tool_list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self.tools):
            tool = self.tools[lv.index]
            result = toggle_favorite(tool.name)
            msg = f"Added '{tool.name}' to favorites" if result else f"Removed '{tool.name}' from favorites"
            self.notify(msg, severity="information")
            self._populate_tools()

    def action_go_back(self):
        self.app.pop_screen()

    def action_search(self):
        self.app.push_screen(SearchScreen())


class ToolDetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "launch", "Launch"),
        Binding("f", "toggle_fav", "Favorite"),
        Binding("i", "info", "Info"),
    ]

    def __init__(self, tool: Tool, **kwargs):
        super().__init__(**kwargs)
        self.tool = tool

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(f"  {self.tool.name}", id="tool_name")
        yield Static(id="tool_detail")
        yield Footer()

    def on_mount(self):
        t = self.tool
        status = "[green]Installed[/green]" if t.installed else "[red]Not Installed[/red]"
        binary_info = f"Binary: {t.binary_path}" if t.binary_path else f"Binary: {t.binary}"
        fav = "★ Favorite" if is_favorite(t.name) else ""
        tags = ", ".join(t.tags) if t.tags else "none"

        detail = (
            f"  {t.description}\n\n"
            f"  Status: {status}\n"
            f"  {binary_info}\n"
            f"  Category: {t.category}\n"
            f"  Tags: {tags}\n"
        )
        if t.documentation:
            detail += f"  Docs: {t.documentation}\n"
        if fav:
            detail += f"\n  {fav}\n"

        detail += (
            f"\n  {'─' * 40}\n"
            f"  [ENTER] Launch  [F] Favorite  [I] Info  [ESC] Back\n"
        )

        self.query_one("#tool_detail").update(detail)

    def action_launch(self):
        if not self.tool.installed:
            self.notify(
                f"'{self.tool.name}' is not installed",
                severity="error",
            )
            return
        self.app.push_screen(ToolLaunchScreen(self.tool))

    def action_toggle_fav(self):
        result = toggle_favorite(self.tool.name)
        msg = f"Added '{self.tool.name}' to favorites" if result else f"Removed '{self.tool.name}' from favorites"
        self.notify(msg, severity="information")
        self.on_mount()

    def action_go_back(self):
        self.app.pop_screen()

    def action_info(self):
        self.notify(
            f"Tool: {self.tool.name} | Category: {self.tool.category}",
            severity="information",
        )


class ToolLaunchScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, tool: Tool, **kwargs):
        super().__init__(**kwargs)
        self.tool = tool

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(f"  Launching: {self.tool.name}", id="launch_title")
        yield RichLog(id="launch_output", highlight=True)
        yield Footer()

    def on_mount(self):
        log = self.query_one("#launch_output", RichLog)
        log.write(f"[bold]Command:[/bold] {self.tool.command}")
        log.write(f"[bold]Binary:[/bold] {self.tool.binary_path}")
        log.write("─" * 40)
        log.write("[yellow]Note: For interactive tools, use your terminal directly.[/yellow]")
        log.write(f"[dim]Run: {self.tool.command}[/dim]")
        log.write("─" * 40)
        log.write("[green]Press ESC to go back[/green]")

    def action_go_back(self):
        self.app.pop_screen()


class SearchScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("  Search Tools", id="search_title")
        yield Input(placeholder="Type to search...", id="search_input")
        yield ListView(id="search_results")
        yield Footer()

    def on_mount(self):
        self.query_one("#search_input").focus()

    def on_input_changed(self, event: Input.Changed):
        query = event.value
        results = search_tools(self.app.tools, query)
        lv = self.query_one("#search_results", ListView)
        lv.clear()
        for tool in results:
            status = "✓" if tool.installed else "✗"
            label = Label(
                f"  {status}  {tool.name}  —  {tool.description[:50]}"
            )
            lv.append(ListItem(label))

    def on_list_view_selected(self, event: ListView.Selected):
        query = self.query_one("#search_input").value
        results = search_tools(self.app.tools, query)
        if 0 <= event.item_index < len(results):
            self.app.push_screen(ToolDetailScreen(results[event.item_index]))

    def action_go_back(self):
        self.app.pop_screen()


class FavoritesScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "select_tool", "Details"),
        Binding("f", "remove_fav", "Remove Favorite"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools: list[Tool] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("  Favorites", id="fav_title")
        yield ListView(id="fav_list")
        yield Footer()

    def on_mount(self):
        fav_names = get_favorites()
        self.tools = [
            t for t in self.app.tools if t.name in fav_names
        ]
        lv = self.query_one("#fav_list", ListView)
        lv.clear()
        for tool in self.tools:
            status = "✓" if tool.installed else "✗"
            label = Label(
                f"  ★  {status}  {tool.name}  —  {tool.description[:50]}"
            )
            lv.append(ListItem(label))

    def on_list_view_selected(self, event: ListView.Selected):
        if 0 <= event.item_index < len(self.tools):
            self.app.push_screen(
                ToolDetailScreen(self.tools[event.item_index])
            )

    def action_select_tool(self):
        lv = self.query_one("#fav_list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self.tools):
            self.app.push_screen(
                ToolDetailScreen(self.tools[lv.index])
            )

    def action_remove_fav(self):
        lv = self.query_one("#fav_list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self.tools):
            tool = self.tools[lv.index]
            toggle_favorite(tool.name)
            self.notify(f"Removed '{tool.name}' from favorites")
            self.on_mount()

    def action_go_back(self):
        self.app.pop_screen()


class HistoryScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("  Execution History", id="hist_title")
        yield ListView(id="hist_list")
        yield Footer()

    def on_mount(self):
        history = get_history(limit=50)
        lv = self.query_one("#hist_list", ListView)
        lv.clear()
        if not history:
            lv.append(ListItem(Label("  No history yet")))
            return

        for record in history:
            exit_str = (
                f"exit: {record.exit_code}"
                if record.exit_code >= 0
                else "running"
            )
            icon = "✓" if record.exit_code == 0 else "✗" if record.exit_code > 0 else "●"
            label = Label(
                f"  {icon}  {record.timestamp}  {record.tool_name:<15}  {exit_str}"
            )
            lv.append(ListItem(label))

    def action_go_back(self):
        self.app.pop_screen()


class VoltApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #banner {
        text-align: center;
        color: $primary;
        content-align: center middle;
        height: 7;
    }

    .subtitle {
        text-align: center;
        color: $text-muted;
        text-style: italic;
    }

    .center {
        text-align: center;
    }

    #screen_title {
        text-style: bold;
        color: $primary;
        padding: 0 1;
    }

    #search_title {
        text-style: bold;
        color: $primary;
        padding: 0 1;
    }

    #fav_title {
        text-style: bold;
        color: $primary;
        padding: 0 1;
    }

    #hist_title {
        text-style: bold;
        color: $primary;
        padding: 0 1;
    }

    #tool_name {
        text-style: bold;
        color: $primary;
        padding: 0 1;
    }

    #launch_title {
        text-style: bold;
        color: $warning;
        padding: 0 1;
    }

    #tool_detail {
        padding: 0 1;
        color: $text;
    }

    #status {
        dock: bottom;
        padding: 0 2;
        background: $accent-darken-2;
        color: $text;
        text-style: bold;
    }

    ListView {
        height: 1fr;
    }

    ListItem {
        padding: 0 1;
    }

    ListItem:hover {
        background: $accent-darken-1;
    }

    Input {
        margin: 0 1;
    }

    RichLog {
        height: 1fr;
        padding: 0 1;
    }
    """

    TITLE = "VOLT — Security Toolkit Manager"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools: list[Tool] = []

    def on_mount(self):
        init_db()
        catalog = load_catalog()
        self.tools = detect_all(catalog)
        self.push_screen(MainScreen())

    def get_installed_count(self) -> int:
        return sum(1 for t in self.tools if t.installed)
