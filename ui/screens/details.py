# ui/screens/details.py
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ListView, ListItem, Label, LoadingIndicator
from textual.screen import Screen
from textual import work
from rich.text import Text

from ui.widgets.sidebar import SeriesSidebar
from ui.screens.player import StreamSelectScreen
from ui.widgets.vim_list import VimListView
from core.utils import fmt_runtime

# NEW: Import bindings
from ui.keybinds import NAV_BINDINGS, APP_BINDINGS

class SeriesDetailScreen(Screen):
    # Add Navigation Bindings to this screen
    BINDINGS = NAV_BINDINGS + [
        ("escape", "back", "Back") 
    ]

    CSS = """
    SeriesDetailScreen, #container, #list_pane, VimListView { background: transparent; }
    
    #screen_title {
        dock: top; padding: 1 2; color: #d7005f; 
        text-style: bold; border-bottom: solid #333;
        background: transparent;
    }

    ListItem { padding: 1 2; color: #888; background: transparent; }
    
    /* FIX: Ensure hover works on the item text */
    ListItem:hover { color: #d7005f; background: transparent; }
    
    /* FIX: Changed .--highlight to .-highlight */
    ListItem.-highlight { 
        color: #d7005f; 
        text-style: bold;
        background: transparent;
        border: none;
    }
    
    ListItem.-highlight Label {
        color: #d7005f;
    }
    """

    def __init__(self, imdb_id, title):
        super().__init__()
        self.imdb_id = imdb_id
        self.show_title = title
        self.seasons_map = {} 
        self.sorted_season_keys = []
        self.viewing_seasons = True 
        self.is_single_season = False
        self.meta = {}
        self.main_poster_url = None
        self.series_runtime = "N/A"
        self.loaded_seasons = set()
        self.season_meta_cache = {} 
        self.current_season = None
        
    def compose(self) -> ComposeResult:
        with Horizontal(id="container"):
            yield SeriesSidebar(id="sidebar")
            with Vertical(id="list_pane"):
                yield Label("Fetching Metadata...", id="screen_title")
                yield LoadingIndicator(id="loading")
                
                # SWAP ListView for VimListView
                yield VimListView(id="selection_list")

    def on_mount(self):
        self.manager = self.app.manager
        self.fetch_data()
        # Auto-focus the list so 'j'/'k' works immediately
        self.query_one("#selection_list").focus()

    def action_back(self):
        if not self.viewing_seasons and not self.is_single_season:
            self.show_season_list()
        else:
            self.app.pop_screen()

    @work
    async def fetch_data(self):
        sidebar = self.query_one(SeriesSidebar)
        self.meta = await self.manager.get_unified_metadata(self.imdb_id, self.show_title)
        
        if not self.meta or not self.meta.get('videos'):
            self.query_one("#screen_title").update("Failed to load metadata.")
            self.query_one("#loading").display = False
            return

        self.main_poster_url = self.meta.get('poster')
        self.series_runtime = fmt_runtime(self.meta.get('runtime'))
        
        videos = self.meta.get('videos', [])
        seasons = {}
        for vid in videos:
            s = vid.get('season', 1)
            if s is None: s = 1 
            if s not in seasons: seasons[s] = []
            seasons[s].append(vid)
            
        self.seasons_map = seasons
        valid_keys = [k for k in seasons.keys() if k is not None]
        keys = sorted([k for k in valid_keys if k != 0])
        if 0 in seasons: keys.append(0)
        self.sorted_season_keys = keys

        self.query_one("#screen_title").update("Fetching Season Metadata...")
        
        self.season_meta_cache = await self.manager.fetch_all_season_details(
            self.imdb_id, 
            self.show_title, 
            self.meta.get('genres', []),
            self.meta.get('country', 'Unknown'), 
            keys
        )

        if self.main_poster_url:
            await self.manager.get_image(self.main_poster_url)
            
        count = 0
        for s_num in keys:
            if count >= 10: break
            s_key = int(s_num)
            if s_key in self.season_meta_cache:
                s_poster = self.season_meta_cache[s_key].get('poster')
                if s_poster:
                    await self.manager.get_image(s_poster)
            count += 1

        self.query_one("#loading").display = False
        sidebar.show_series_data(self.meta, self.series_runtime)
        if self.main_poster_url:
            self.load_image_to_sidebar(self.main_poster_url)
        
        if len(keys) == 1 and keys[0] != 0:
            self.is_single_season = True
            self.show_episodes(keys[0])
        else:
            self.show_season_list()

    @work
    async def load_image_to_sidebar(self, url):
        pil_img = await self.manager.get_image(url)
        if pil_img and self.is_mounted:
            self.query_one(SeriesSidebar).update_image(pil_img)

    @work
    async def lazy_load_season(self, season_num):
        if season_num in self.loaded_seasons:
            return

        anilist_rating = None
        if season_num in self.season_meta_cache:
            anilist_rating = self.season_meta_cache[season_num].get('rating')

        ratings_map = await self.manager.fetch_season_ratings(self.imdb_id, season_num)
        
        eps = self.seasons_map.get(season_num, [])
        for ep in eps:
            ep_num = int(ep.get('episode', -1))
            if ep_num in ratings_map:
                ep['rating'] = ratings_map[ep_num]
            elif anilist_rating:
                ep['rating'] = anilist_rating
        
        self.loaded_seasons.add(season_num)
        
        if not self.viewing_seasons and self.current_season == season_num:
             list_view = self.query_one("#selection_list")
             if list_view.highlighted_child:
                 self.on_list_view_highlighted(ListView.Highlighted(list_view, list_view.highlighted_child))

        self.prefetch_images(season_num)

    @work
    async def prefetch_images(self, season_num):
        eps = self.seasons_map.get(season_num, [])
        target_eps = eps[:25]
        for ep in target_eps:
            url = ep.get('thumbnail')
            if url:
                await self.manager.get_image(url)

    def show_season_list(self):
        self.viewing_seasons = True
        self.current_season = None
        
        self.query_one("#screen_title").update(f"Select Season")
        self.query_one(SeriesSidebar).show_series_data(self.meta, self.series_runtime)
        if self.main_poster_url:
            self.load_image_to_sidebar(self.main_poster_url)
        
        list_view = self.query_one("#selection_list")
        list_view.clear()
        
        for s in self.sorted_season_keys:
            name = "Extras" if s == 0 else f"Season {s}"
            item = ListItem(Label(name))
            item.season_number = s 
            item.ep_data = None 
            list_view.append(item)
        
        list_view.index = 0
        list_view.focus()

    def show_episodes(self, season_num):
        self.viewing_seasons = False
        self.current_season = season_num
        name = "Extras" if season_num == 0 else f"Season {season_num}"
        self.query_one("#screen_title").update(f"{name}")
        
        self.lazy_load_season(season_num)
        
        list_view = self.query_one("#selection_list")
        list_view.clear()
        
        eps = sorted(self.seasons_map[season_num], key=lambda x: x.get('episode') or 999)
        for ep in eps:
            num = ep.get('episode')
            num_str = f"{num:02d}" if num is not None else "??"
            ep_name = ep.get('name') or "Unknown"
            
            display_text = Text()
            display_text.append(f"{num_str}", style="bold white")
            display_text.append(" | ", style="dim")
            display_text.append(f"{ep_name}", style="#cccccc")
            
            item = ListItem(Label(display_text))
            item.ep_data = ep 
            list_view.append(item)
        
        list_view.index = 0
        list_view.focus()

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        item = message.item
        if item is None: return
        
        sidebar = self.query_one(SeriesSidebar)

        if hasattr(item, 'ep_data') and item.ep_data:
            ep = item.ep_data
            sidebar.show_episode_data(ep, self.series_runtime)
            
            image_to_show = self.main_poster_url
            if ep.get('thumbnail'):
                image_to_show = ep.get('thumbnail')
            elif self.current_season in self.season_meta_cache:
                s_poster = self.season_meta_cache[self.current_season].get('poster')
                if s_poster:
                    image_to_show = s_poster

            self.load_image_to_sidebar(image_to_show)

        elif self.viewing_seasons:
            raw_num = getattr(item, 'season_number', None)
            if raw_num is not None:
                season_num = int(raw_num)
                img_to_show = self.main_poster_url
                
                if season_num in self.season_meta_cache:
                    s_data = self.season_meta_cache[season_num]
                    if s_data.get('poster'):
                        img_to_show = s_data.get('poster')
                    
                    temp_meta = self.meta.copy()
                    if s_data.get('overview'):
                        temp_meta['description'] = s_data['overview']
                        temp_meta['name'] = f"{self.show_title} (Season {season_num})"
                    
                    sidebar.show_series_data(temp_meta, self.series_runtime)
                else:
                    sidebar.show_series_data(self.meta, self.series_runtime)

                self.load_image_to_sidebar(img_to_show)

    def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        if self.viewing_seasons:
            self.show_episodes(item.season_number)
        else:
            ep = getattr(item, 'ep_data', None)
            if ep:
                self.app.push_screen(
                    StreamSelectScreen(
                        imdb_id=self.imdb_id,
                        type_="series",
                        title=self.show_title,
                        season=ep['season'],
                        episode=ep['episode']
                    )
                )
