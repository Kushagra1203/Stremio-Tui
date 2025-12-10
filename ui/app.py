# ui/app.py
import subprocess
import tempfile
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Input, ListView
from textual.binding import Binding

from core.manager import MediaManager
from ui.widgets.nav import SidebarNav, SidebarItem
from ui.widgets.cards import ResultItem
from ui.screens.details import SeriesDetailScreen
from ui.screens.player import StreamSelectScreen
from ui.widgets.vim_list import VimListView

# IMPORT BINDINGS
from ui.keybinds import APP_BINDINGS, NAV_BINDINGS

# --- NEW: Custom List that handles Vim Keys ---
class VimListView(ListView):
    BINDINGS = NAV_BINDINGS

class StremioApp(App):
    CSS_PATH = "../styles.tcss" 

    BINDINGS = APP_BINDINGS

    def __init__(self):
        super().__init__()
        self.manager = MediaManager()
        self.current_view = "search"

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Label("STREMIO TUI", id="sidebar_title")
            yield SidebarNav()

        with Vertical(id="main_container"):
            yield Input(placeholder="Search Movies & TV... (Press 'i' or '/')", id="search_box")
            
            # USE THE IMPORTED WIDGET
            yield VimListView(id="results_list")
            
    def on_mount(self):
        # REMOVED: The crashing .bind() lines
        # Focus search immediately on launch
        self.query_one("#search_box").focus()

    # --- ACTIONS ---
    def action_focus_search(self):
        """Press 'i' or '/' to jump here"""
        self.query_one("#search_box").focus()
        self.notify("Insert Mode")

    def action_focus_list(self):
        """Press 'Esc' to jump here"""
        self.query_one("#results_list").focus()

    # --- EVENT HANDLERS ---
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
            list_view.append(ResultItem(res['title'], res['year'], res['type'], res['id']))
        
        # LOGIC: Auto-select first result and switch focus to list
        if len(list_view.children) > 0:
            list_view.index = 0  # Highlight first item
            list_view.focus()    # Move focus from Input to List

    async def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        
        # Sidebar Navigation Logic
        if isinstance(item, SidebarItem):
            if item.id_name == "nav_search":
                self.switch_to_search()
            elif item.id_name == "nav_trending":
                await self.switch_to_trending()
            elif item.id_name == "nav_history":
                self.switch_to_history()

        # Result Selection Logic
        elif isinstance(item, ResultItem):
            if item.stream_link:
                self.play_video(item)
                return 

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

    def play_video(self, item):
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

    def switch_to_search(self):
        self.current_view = "search"
        search_box = self.query_one("#search_box")
        search_box.remove_class("hidden")
        self.query_one("#results_list").clear()
        search_box.focus()

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
            list_view.append(ResultItem(res['title'], res['year'], res['type'], res['id']))
        
        # Auto-focus list
        list_view.focus()
        list_view.index = 0

    def switch_to_history(self):
        self.current_view = "history"
        self.query_one("#search_box").add_class("hidden")
        list_view = self.query_one("#results_list")
        list_view.clear()
        
        history_items = self.manager.get_history()
        
        for item in history_items:
            base_title = item['title'] 
            info_str = item.get('last_watched', '')
            if item.get('season') and item.get('episode'):
                info_str = f"S{item['season']:02d}E{item['episode']:02d} | {info_str}"

            list_view.append(
                ResultItem(
                    title=base_title,
                    year=info_str, 
                    type_=item.get('type', 'series'),
                    imdb_id=item['imdb_id'],
                    stream_link=item.get('stream_link')
                )
            )
        list_view.focus()
        list_view.index = 0

    async def on_shutdown(self):
        await self.manager.close()
