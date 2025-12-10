# ui/widgets/nav.py
from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

class SidebarItem(ListItem):
    def __init__(self, label, id_name):
        super().__init__()
        self.label_text = label
        self.id_name = id_name

    def compose(self) -> ComposeResult:
        # Simple text, no emoji
        yield Label(f" {self.label_text}") 

class SidebarNav(Static):
    def compose(self) -> ComposeResult:
        with ListView(id="sidebar_nav"):
            yield SidebarItem("SEARCH", "nav_search")
            yield SidebarItem("TRENDING", "nav_trending")
            yield SidebarItem("HISTORY", "nav_history")
