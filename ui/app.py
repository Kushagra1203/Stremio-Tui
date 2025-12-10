# ui/app.py
import subprocess # <--- Needed for launching MPV
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Input, ListView, Footer
from textual.binding import Binding

from core.manager import MediaManager
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
        self.current_view = "search"

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Label("STREMIO TUI", id="sidebar_title")
            yield SidebarNav()

        with Vertical(id="main_container"):
            yield Input(placeholder="Search Movies & TV...", id="search_box")
            yield ListView(id="results_list")
        
        yield Footer()

    def on_mount(self):
        self.query_one("#search_box").focus()

    async def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        
        # CASE A: Sidebar Navigation
        if isinstance(item, SidebarItem):
            if item.id_name == "nav_search":
                self.switch_to_search()
            elif item.id_name == "nav_trending":
                await self.switch_to_trending()
            elif item.id_name == "nav_history":
                self.switch_to_history()

        # CASE B: Result Item (Movie/Show)
        elif isinstance(item, ResultItem):
            # --- NEW: Direct Play from History ---
            if item.stream_link:
                self.notify(f"Resuming {item.title_text}...")
                with self.suspend():
                    subprocess.run(["clear"])
                    # Use the same command flags as the Player screen
                    cmd = [
                        "webtorrent", item.stream_link, 
                        "--mpv", 
                        "--player-args=--save-position-on-quit" 
                    ]
                    subprocess.run(cmd)
                return 
            # -------------------------------------

            # Normal Navigation
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

    def switch_to_search(self):
        self.current_view = "search"
        search_box = self.query_one("#search_box")
        search_box.remove_class("hidden")
        search_box.focus()
        self.query_one("#results_list").clear()
        self.notify("Search Mode")

    async def switch_to_trending(self):
        self.current_view = "trending"
        self.query_one("#search_box").add_class("hidden")
        
        list_view = self.query_one("#results_list")
        list_view.clear()
        self.notify("Fetching Trending Series...")
        
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
        list_view.focus()

    def switch_to_history(self):
        self.current_view = "history"
        self.query_one("#search_box").add_class("hidden")
        
        list_view = self.query_one("#results_list")
        list_view.clear()
        
        history_items = self.manager.get_history()
        
        if not history_items:
            self.notify("No history found.")
            return

        self.notify(f"Loaded {len(history_items)} items.")
        
        for item in history_items:
            # --- FIX: Cleaner Formatting ---
            clean_title = item['title']
            
            # Use 'Last Watched' as the subtitle/year
            timestamp = item.get('last_watched', '')
            
            # If it's a series, append info to TITLE, not create duplicates
            if item.get('season') and item.get('episode'):
                s_num = item['season']
                e_num = item['episode']
                clean_title = f"{clean_title} - S{s_num:02d}E{e_num:02d}"

            list_view.append(
                ResultItem(
                    title=clean_title,
                    year=timestamp, 
                    type_=item.get('type', 'series'),
                    imdb_id=item['imdb_id'],
                    stream_link=item.get('stream_link') # Pass the link!
                )
            )
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

