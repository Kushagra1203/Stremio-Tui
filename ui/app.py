# ui/app.py
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Input, ListView, Footer
from textual.binding import Binding

from core.manager import MediaManager
# --- FIX: Ensure SidebarItem is imported here ---
from ui.widgets.nav import SidebarNav, SidebarItem
from ui.widgets.cards import ResultItem
from ui.screens.details import SeriesDetailScreen
from ui.screens.player import StreamSelectScreen

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

    /* --- UTILITIES --- */
    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("slash", "focus_search", "Search"),
    ]

    def __init__(self):
        super().__init__()
        self.manager = MediaManager()
        self.current_view = "search" # Track what we are looking at

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Label("STREMIO TUI", id="sidebar_title")
            yield SidebarNav()

        with Vertical(id="main_container"):
            # We keep the Input but might hide it
            yield Input(placeholder="Search Movies & TV...", id="search_box")
            
            # This list will hold Search Results OR Trending Items
            yield ListView(id="results_list")
        
        yield Footer()

    def on_mount(self):
        self.query_one("#search_box").focus()

    # --- Handle Sidebar Clicks ---
    async def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        
        # CASE A: Sidebar Navigation Clicked
        if isinstance(item, SidebarItem):
            if item.id_name == "nav_search":
                self.switch_to_search()
            elif item.id_name == "nav_trending":
                await self.switch_to_trending()
            # History/Settings can be added later

        # CASE B: Result Item Clicked (Movie/Show)
        elif isinstance(item, ResultItem):
            if hasattr(item, 'type_'):
                if item.type_ == "TV series" or item.type_ == "series":
                    self.push_screen(SeriesDetailScreen(item.imdb_id, item.title_text))
                else:
                    self.push_screen(
                        StreamSelectScreen(
                            imdb_id=item.imdb_id,
                            type_=item.type_,
                            title=item.title_text
                        )
                    )

    # --- View Logic ---
    def switch_to_search(self):
        self.current_view = "search"
        search_box = self.query_one("#search_box")
        search_box.remove_class("hidden")
        search_box.focus()
        
        # Clear list or keep previous search results? Let's clear for now
        self.query_one("#results_list").clear()
        self.notify("Search Mode")

    async def switch_to_trending(self):
        self.current_view = "trending"
        
        # Hide Search Box
        self.query_one("#search_box").add_class("hidden")
        
        # Clear List & Fetch Trending
        list_view = self.query_one("#results_list")
        list_view.clear()
        self.notify("Fetching Trending Series...")
        
        # Fetch Data
        results = await self.manager.get_trending("series")
        
        if not results:
            self.notify("Failed to load Trending.", severity="error")
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
        
        # Focus the list so user can scroll immediately
        list_view.focus()

    async def on_input_submitted(self, message: Input.Submitted):
        query = message.value
        if not query: return
        
        list_view = self.query_one("#results_list")
        list_view.clear()
        
        self.notify(f"Searching for {query}...")
        results = await self.manager.search_imdb(query)
        
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

    async def on_shutdown(self):
        await self.manager.close()

