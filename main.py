# main.py
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Input, ListView, Label, ListItem, Static
from textual.binding import Binding
from rich.text import Text

# --- UPDATED IMPORTS ---
from core import StremioClient
from screens_episodes import SeriesDetailScreen
from screens_torrent import StreamSelectScreen

# ... (Rest of main.py stays mostly the same, just paste the classes below)

class SidebarItem(ListItem):
    """A selectable item in the sidebar."""
    def __init__(self, label, icon, id_name):
        super().__init__()
        self.label_text = label
        self.icon = icon
        self.id_name = id_name

    def compose(self) -> ComposeResult:
        yield Label(f"{self.icon} {self.label_text}")

class ResultItem(ListItem):
    """Search Result Item (Moved here since it's used in Main)"""
    def __init__(self, title, year, type_, imdb_id):
        super().__init__()
        self.title_text = title
        self.year = year
        self.type_ = type_ 
        self.imdb_id = imdb_id

    def compose(self) -> ComposeResult:
        t = Text(f"{self.title_text} ({self.year})", style="bold blue")
        yield Label(t)
        yield Label(f"{self.type_}", classes="result_type")

class Sidebar(Static):
    """The left navigation pane."""
    def compose(self) -> ComposeResult:
        with ListView(id="sidebar_nav"):
            yield SidebarItem("Search", "🔍", "nav_search")
            yield SidebarItem("Trending", "🔥", "nav_trending")
            yield SidebarItem("History", "📜", "nav_history")
            yield SidebarItem("Settings", "⚙️", "nav_settings")

class StremioApp(App):
    CSS = """
    /* --- GLOBAL LAYOUT --- */
    Screen {
        layout: horizontal;
        background: #121212;
        color: #e0e0e0;
    }

    /* --- SIDEBAR --- */
    #sidebar {
        width: 25;
        dock: left;
        background: #1a1a1a;
        border-right: solid #333;
        height: 100%;
    }

    #sidebar_title {
        text-align: center;
        padding: 1;
        color: #d7005f;
        text-style: bold;
        background: #1a1a1a;
        border-bottom: solid #333;
    }

    #sidebar_nav {
        background: #1a1a1a;
        border: none;
    }

    SidebarItem {
        padding: 1 2;
        background: #1a1a1a;
        color: #888;
    }

    SidebarItem:hover {
        background: #262626;
        color: #fff;
    }

    /* --- MAIN CONTENT AREA --- */
    #main_container {
        width: 1fr;
        height: 100%;
        padding: 1 2;
    }

    Input {
        dock: top;
        margin-bottom: 1;
        border: tall #333;
        background: #121212;
        color: #fff;
    }
    
    #results_list {
        background: #121212;
        border: none;
    }
    
    ResultItem {
        padding: 1;
        border-bottom: solid #222;
    }
    ResultItem:hover {
        background: #1e1e1e;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("slash", "focus_search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self.client = StremioClient()

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Label("STREMIO TUI", id="sidebar_title")
            yield Sidebar()

        with Vertical(id="main_container"):
            yield Input(placeholder="Search Movies & TV...", id="search_box")
            yield ListView(id="results_list")
        
        yield Footer()

    def on_mount(self):
        self.query_one("#search_box").focus()

    async def on_input_submitted(self, message: Input.Submitted):
        query = message.value
        if not query: return
        
        list_view = self.query_one("#results_list")
        list_view.clear()
        
        self.notify(f"Searching for {query}...")
        results = await self.client.search_imdb(query)
        
        if not results:
            self.notify("No results found.", severity="error")
            return

        for res in results:
            list_view.append(
                ResultItem(
                    title=res['title'],
                    year=res['year'],
                    type_=res['type'],
                    imdb_id=res['id']
                )
            )

    def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        if isinstance(item, ResultItem):
            if hasattr(item, 'type_'):
                if item.type_ == "TV series":
                    self.push_screen(SeriesDetailScreen(item.imdb_id, item.title_text))
                else:
                    self.push_screen(
                        StreamSelectScreen(
                            imdb_id=item.imdb_id,
                            type_=item.type_,
                            title=item.title_text
                        )
                    )

    async def on_shutdown(self):
        await self.client.close()

if __name__ == "__main__":
    app = StremioApp()
    app.run()
