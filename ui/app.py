# ui/app.py
import subprocess
import tempfile
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Input, ListView, LoadingIndicator
from textual import work
from textual.css.query import NoMatches

from core.manager import MediaManager
from ui.widgets.nav import SidebarNav, SidebarItem
from ui.widgets.cards import ResultItem
from ui.screens.details import SeriesDetailScreen
from ui.screens.player import StreamSelectScreen
from ui.widgets.vim_list import VimListView
from ui.widgets.sidebar import SeriesSidebar

from ui.keybinds import APP_BINDINGS

class StremioApp(App):
    CSS_PATH = "../styles.tcss" 
    BINDINGS = APP_BINDINGS

    def __init__(self):
        super().__init__()
        self.manager = MediaManager()
        self.current_view = "search"
        self.preview_cache = {} 

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Label("STREMIO TUI", id="sidebar_title")
            yield SidebarNav()

        with Vertical(id="main_container"):
            yield Input(placeholder="Search Movies & TV... (Press 'i' or '/')", id="search_box")
            
            # Use a Container to stack the Loading Indicator and the Content
            with Container(id="results_area"):
                
                # 1. The Loading Screen (Hidden by default)
                yield LoadingIndicator(id="main_loading", classes="hidden")
                
                # 2. The Content Area (List + Preview)
                with Horizontal(id="content_view"):
                    yield VimListView(id="results_list")
                    yield SeriesSidebar(id="home_preview")
            
    def on_mount(self):
        self.query_one("#search_box").focus()

    # --- ACTIONS ---
    def action_focus_search(self):
        self.query_one("#search_box").focus()
        self.notify("Insert Mode")

    def action_focus_list(self):
        self.query_one("#results_list").focus()

    # --- CORE LOGIC: PRE-FETCHING ---
    async def prefetch_metadata(self, results, limit=20):
        """Fetch metadata and posters for the top N results before rendering.

        Metadata is what makes the list usable (title, year, poster), so it is
        fetched up front in parallel rather than lazily as the cursor moves.
        Posters are queued afterwards because they are the slowest part and the
        UI reads fine without them for the first few hundred milliseconds.
        """
        pending = [
            item for item in results[:limit]
            if item["id"] not in self.preview_cache
        ]
        if not pending:
            return

        # Pair each item with its own result. Zipping here (rather than indexing
        # back into `pending` with the result's position) is what keeps the
        # cache correct when some items were already cached and skipped.
        metas = await asyncio.gather(
            *(self.manager.get_unified_metadata(item["id"], item["title"])
              for item in pending)
        )

        posters = []
        for item, meta in zip(pending, metas):
            if not meta:
                continue
            self.preview_cache[item["id"]] = meta
            if meta.get("poster"):
                posters.append(meta["poster"])

        if posters:
            await asyncio.gather(*(self.manager.get_image(url) for url in posters))

    # --- EVENT HANDLERS ---
    
    async def on_input_submitted(self, message: Input.Submitted):
        query = message.value
        if not query: return
        
        self.set_loading(True)
        self.notify(f"Searching for {query}...")
        
        results = await self.manager.search_imdb(query)
        
        if not results:
            self.notify("No results found.", severity="error")
            self.set_loading(False)
            return

        # PRE-FETCH BEFORE SHOWING
        await self.prefetch_metadata(results)

        self.populate_list(results)
        self.set_loading(False)

    async def switch_to_trending(self):
        self.current_view = "trending"
        self.query_one("#search_box").add_class("hidden")
        
        self.set_loading(True)
        self.notify("Fetching Trending Series...")
        
        results = await self.manager.get_trending("series")
        
        if not results:
            self.notify("Failed to load Trending.", severity="error")
            self.set_loading(False)
            return

        # PRE-FETCH BEFORE SHOWING
        await self.prefetch_metadata(results, limit=25) # Fetch top 25

        self.populate_list(results)
        self.set_loading(False)

    # --- HELPERS ---
    def set_loading(self, is_loading):
        loader = self.query_one("#main_loading")
        content = self.query_one("#content_view")
        
        if is_loading:
            content.add_class("hidden")
            loader.remove_class("hidden")
        else:
            loader.add_class("hidden")
            content.remove_class("hidden")

    def populate_list(self, results):
        list_view = self.query_one("#results_list")
        list_view.clear()
        for res in results:
            list_view.append(ResultItem(res['title'], res['year'], res['type'], res['id']))
        
        if len(list_view.children) > 0:
            list_view.index = 0
            list_view.focus()

    # --- SIDEBAR UPDATES ---
    async def on_list_view_highlighted(self, message: ListView.Highlighted):
        item = message.item
        if isinstance(item, ResultItem):
            # No await here, @work handles it
            self.update_preview_sidebar(item)

    @work
    async def update_preview_sidebar(self, item: ResultItem):
        try:
            sidebar = self.query_one("#home_preview", SeriesSidebar)
        except NoMatches:
            return

        # 1. Check Cache (This should hit 99% of time now!)
        if item.imdb_id in self.preview_cache:
            meta = self.preview_cache[item.imdb_id]
            sidebar.show_series_data(meta, str(meta.get('runtime', '')))
            if meta.get('poster'):
                await self.load_image_to_sidebar(meta.get('poster'))
            return

        # 2. Fallback if not cached (scrolled past pre-fetched limit)
        partial_meta = {
            "name": item.title_text,
            "year": item.year,
            "status": "Loading...",
            "description": "Fetching details...",
            "rating": "",
            "genres": []
        }
        sidebar.show_series_data(partial_meta, "")

        meta = await self.manager.get_unified_metadata(item.imdb_id, item.title_text)
        if meta:
            self.preview_cache[item.imdb_id] = meta
            sidebar.show_series_data(meta, str(meta.get('runtime', '')))
            if meta.get('poster'):
                await self.load_image_to_sidebar(meta.get('poster'))

    async def load_image_to_sidebar(self, url):
        pil_img = await self.manager.get_image(url)
        if pil_img:
            try:
                self.query_one("#home_preview", SeriesSidebar).update_image(pil_img)
            except NoMatches:
                pass

    # --- REST OF THE METHODS (Navigation, Player) ---
    async def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        if isinstance(item, SidebarItem):
            if item.id_name == "nav_search":
                self.switch_to_search()
            elif item.id_name == "nav_trending":
                await self.switch_to_trending()
            elif item.id_name == "nav_history":
                self.switch_to_history()
        elif isinstance(item, ResultItem):
            if item.stream_link:
                self.play_video(item)
                return 
            if hasattr(item, 'type_'):
                if item.type_ in ["TV series", "series"]:
                    self.push_screen(SeriesDetailScreen(item.imdb_id, item.title_text))
                else:
                    self.push_screen(StreamSelectScreen(item.imdb_id, item.type_, item.title_text))

    def play_video(self, item):
        self.notify(f"Resuming {item.title_text}...")
        with self.suspend():
            subprocess.run(["clear"])
            with tempfile.TemporaryDirectory(prefix="stremio_") as tmp_dir:
                cmd = ["webtorrent", item.stream_link, "--out", tmp_dir, "--mpv", "--player-args=--save-position-on-quit"]
                subprocess.run(cmd)

    def switch_to_search(self):
        self.current_view = "search"
        search_box = self.query_one("#search_box")
        search_box.remove_class("hidden")
        self.query_one("#results_list").clear()
        search_box.focus()

    def switch_to_history(self):
        self.current_view = "history"
        self.query_one("#search_box").add_class("hidden")
        list_view = self.query_one("#results_list")
        list_view.clear()
        # History is instant, no need to prefetch heavy metadata
        for item in self.manager.get_history():
            base_title = item['title'] 
            info_str = item.get('last_watched', '')
            if item.get('season') and item.get('episode'):
                info_str = f"S{item['season']:02d}E{item['episode']:02d} | {info_str}"
            list_view.append(ResultItem(base_title, info_str, item.get('type', 'series'), item['imdb_id'], item.get('stream_link')))
        list_view.focus()
        list_view.index = 0

    async def on_shutdown(self):
        await self.manager.close()
