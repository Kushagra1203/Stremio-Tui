# ui/widgets/nav.py
from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

class SidebarItem(ListItem):
    """A selectable item in the sidebar."""
    def __init__(self, label, icon, id_name):
        super().__init__()
        self.label_text = label
        self.icon = icon
        self.id_name = id_name

    def compose(self) -> ComposeResult:
        yield Label(f"{self.icon} {self.label_text}")

class SidebarNav(Static):
    """The left navigation pane."""
    def compose(self) -> ComposeResult:
        with ListView(id="sidebar_nav"):
            yield SidebarItem("Search", "🔍", "nav_search")
            yield SidebarItem("Trending", "🔥", "nav_trending")
            yield SidebarItem("History", "📜", "nav_history")
