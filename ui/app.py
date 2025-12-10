# ui/app.py
import subprocess
import tempfile
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
    CSS_PATH = "../styles.tcss" 

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
            # Direct Play
            if item.stream_link:
                self.notify(f"Resuming {item.title_text}...")
                with self.suspend():
                    subprocess.run(["clear"])
                    with tempfile.TemporaryDirectory(prefix="stremio_") as tmp_dir:
                        cmd = [
                            "webtorrent", item.stream_link, 
                            "--out", tmp_dir, 
                            "--mpv", 
                            "--player-args=--save-position-on-quit" 
                        ]
                        subprocess.run(cmd)
                return 

            # Navigation
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
            clean_title = item['title']
            timestamp = item.get('last_watched', '')
            
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
                    stream_link=item.get('stream_link')
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
