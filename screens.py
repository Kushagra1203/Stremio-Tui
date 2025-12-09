# screens.py
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, LoadingIndicator, Static
from textual.screen import Screen
from textual import work
from rich.text import Text
import re
import subprocess

# Import helpers
from core import format_size, get_magnet_name

# --- WIDGETS ---
class ResultItem(ListItem):
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

class StreamItem(ListItem):
    def __init__(self, display_renderable, link):
        super().__init__()
        self.display_renderable = display_renderable
        self.link = link

    def compose(self) -> ComposeResult:
        yield Label(self.display_renderable)

# --- SCREEN 1: TORRENT LIST (PRESERVED) ---
class StreamSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    
    CSS = """
    StreamSelectScreen ListView {
        scrollbar-size-vertical: 0;
    }
    """

    def __init__(self, imdb_id, type_, title, season=None, episode=None):
        super().__init__()
        self.imdb_id = imdb_id
        self.type_ = "movie" if type_ == "feature" else "series"
        self.media_title = title
        self.season = season
        self.episode = episode
        
        if self.type_ == "series":
            self.stremio_id = f"{imdb_id}:{season}:{episode}"
            self.display_title = f"{title} - S{season:02d}E{episode:02d}"
        else:
            self.stremio_id = imdb_id
            self.display_title = title

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Fetching Streams: {self.display_title}", id="screen_title")
        yield LoadingIndicator(id="loading")
        yield ListView(id="stream_list")
        yield Footer()

    def on_mount(self):
        self.fetch_streams()

    @work
    async def fetch_streams(self):
        app = self.app 
        streams = await app.client.get_all_streams(self.type_, self.stremio_id)
        
        list_view = self.query_one("#stream_list")
        loading = self.query_one("#loading")
        title_label = self.query_one("#screen_title")
        
        loading.display = False
        
        if not streams:
            title_label.update(f"No streams found for {self.display_title}")
            return

        title_label.update(f"Select Stream: {self.display_title} ({len(streams)} found)")
        
        available_width = app.console.size.width - 6

        for s in streams:
            # 1. Provider Tag
            raw_provider = s.get('name', 'UNK').replace('\n', ' ')
            if "Torrentio" in raw_provider: provider_tag = "Tor"
            elif "Comet" in raw_provider: provider_tag = "Comet"
            else: provider_tag = raw_provider[:5]

            # 2. Title & Parsing
            full_title = s.get('title', '')
            bh = s.get('behaviorHints', {})
            
            if '\n' in full_title: filename = full_title.split('\n')[0]
            else: filename = full_title
            
            if not filename: filename = bh.get('filename')
            if not filename: filename = "Unknown Release"

            # 3. Resolution
            check_str = (full_title + " " + raw_provider).lower()
            res_tag = ""
            res_color = "dim"
            
            if "2160p" in check_str or "4k" in check_str:
                res_tag = "4K"
                res_color = "bold gold1"
            elif "1080p" in check_str:
                res_tag = "1080p"
                res_color = "bold green"
            elif "720p" in check_str:
                res_tag = "720p"
                res_color = "green"
            elif "480p" in check_str:
                res_tag = "480p"
                res_color = "yellow"
            elif "cam" in check_str:
                res_tag = "CAM"
                res_color = "red"

            # 4. Stats Hunter
            info_parts = []
            size_found = False
            if bh.get('videoSize'):
                info_parts.append(f"💾 {format_size(bh.get('videoSize'))}")
                size_found = True
            
            if not size_found:
                size_match = re.search(r'(\d+(?:\.\d+)?\s?[KMGT]B)', full_title, re.IGNORECASE)
                if size_match: info_parts.append(f"💾 {size_match.group(1).upper()}")

            seed_found = False
            if s.get('seeds') is not None:
                 info_parts.append(f"👤 {s['seeds']}")
                 seed_found = True
            
            if not seed_found:
                 seed_match = re.search(r'👤\s?(\d+)', full_title)
                 if seed_match: info_parts.append(f"👤 {seed_match.group(1)}")

            stats_str = "  ".join(info_parts)

            # 5. Truncation
            prefix_len = len(provider_tag) + 3 
            if res_tag: prefix_len += len(res_tag) + 3
            suffix_len = len(stats_str) + 3
            reserved = prefix_len + suffix_len
            title_space = available_width - reserved
            if title_space < 15: title_space = 15
            
            clean_name = filename.strip()
            if len(clean_name) > title_space:
                 display_name = clean_name[:title_space-1] + "…"
            else:
                 display_name = clean_name

            # 6. Build Text
            final_text = Text()
            final_text.append(f"[{provider_tag}] ", style="bold blue")
            if res_tag: final_text.append(f"[{res_tag}] ", style=res_color)
            final_text.append(display_name)
            if stats_str:
                final_text.append(" | ", style="dim")
                final_text.append(stats_str, style="cyan")

            link = s.get('url') or s.get('infoHash')
            if not link: continue
            
            if not link.startswith("magnet") and not link.startswith("http"):
                link = f"magnet:?xt=urn:btih:{link}"
            
            list_view.append(StreamItem(final_text, link))

    def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        link = item.link 
        self.app.notify(f"Launching WebTorrent...")
        with self.app.suspend():
            subprocess.run(["clear"]) 
            subprocess.run(["webtorrent", link, "--mpv"])


# --- SCREEN 2: EPISODE/SEASON SELECTOR (UPGRADED LAYOUT) ---
class SeriesDetailScreen(Screen):
    CSS = """
    SeriesDetailScreen {
        align: center middle;
    }

    #container {
        width: 100%;
        height: 100%;
        layout: horizontal;
    }

    /* Left Info Pane */
    #info_pane {
        width: 30%;
        height: 100%;
        border-right: solid #333;
        padding: 1 2;
        background: #1a1a1a;
    }

    #info_title {
        text-style: bold;
        color: #d7005f;
        border-bottom: solid #333;
        padding-bottom: 1;
        margin-bottom: 1;
    }

    #info_meta {
        color: #888;
        margin-bottom: 1;
    }

    #info_desc {
        color: #ccc;
    }

    /* Right List Pane */
    #list_pane {
        width: 70%;
        height: 100%;
    }

    #selection_list {
        scrollbar-size-vertical: 0;
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

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(id="container"):
            # LEFT SIDE: Info
            with Vertical(id="info_pane"):
                yield Label(f"{self.show_title}", id="info_title")
                yield Label("Loading details...", id="info_meta")
                yield Static("", id="info_desc")
            
            # RIGHT SIDE: List
            with Vertical(id="list_pane"):
                yield Label("Loading...", id="screen_title")
                yield LoadingIndicator(id="loading")
                yield ListView(id="selection_list")
        
        yield Footer()

    def on_mount(self):
        self.fetch_episodes()

    @work
    async def fetch_episodes(self):
        app = self.app
        self.meta = await app.client.get_series_details(self.imdb_id)
        videos = self.meta.get('videos', [])
        
        # --- UPDATE INFO PANE ---
        year = self.meta.get('year', 'N/A')
        status = self.meta.get('status', 'Unknown').title()
        runtime = self.meta.get('runtime', 'N/A')
        desc = self.meta.get('description', 'No description available.')
        
        # Update UI
        self.query_one("#info_title").update(self.meta.get('name', self.show_title))
        self.query_one("#info_meta").update(f"📅 {year}\n⏱️ {runtime}\n📺 {status}")
        self.query_one("#info_desc").update(desc)

        # --- PROCESS EPISODES ---
        seasons = {}
        for vid in videos:
            s = vid.get('season', 1)
            if s not in seasons: seasons[s] = []
            seasons[s].append(vid)
            
        self.seasons_map = seasons
        keys = sorted([k for k in seasons.keys() if k != 0])
        if 0 in seasons: keys.append(0)
        self.sorted_season_keys = keys

        loading = self.query_one("#loading")
        loading.display = False
        
        if len(keys) == 1:
            self.is_single_season = True
            self.show_episodes(keys[0])
        else:
            self.show_season_list()

    def show_season_list(self):
        self.viewing_seasons = True
        title = self.query_one("#screen_title")
        title.update(f"Select Season")
        
        list_view = self.query_one("#selection_list")
        list_view.clear()
        
        for s in self.sorted_season_keys:
            name = "Extras" if s == 0 else f"Season {s}"
            item = ListItem(Label(Text(name)))
            item.season_number = s 
            list_view.append(item)

    def show_episodes(self, season_num):
        self.viewing_seasons = False
        title = self.query_one("#screen_title")
        name = "Extras" if season_num == 0 else f"Season {season_num}"
        title.update(f"{name}")
        
        list_view = self.query_one("#selection_list")
        list_view.clear()
        
        eps = sorted(self.seasons_map[season_num], key=lambda x: x.get('episode', 0))
        
        for ep in eps:
            num = ep.get('episode')
            ep_name = ep.get('name') or f"Episode {num}"
            display = f"E{num:02d} | {ep_name}"
            
            item = ListItem(Label(Text(display)))
            item.ep_data = ep 
            list_view.append(item)

    def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        
        if self.viewing_seasons:
            self.show_episodes(item.season_number)
        else:
            ep = item.ep_data 
            self.app.push_screen(
                StreamSelectScreen(
                    imdb_id=self.imdb_id,
                    type_="series",
                    title=self.show_title,
                    season=ep['season'],
                    episode=ep['episode']
                )
            )

    def on_key(self, event):
        if event.key == "escape":
            if not self.viewing_seasons and not self.is_single_season:
                self.show_season_list()
            else:
                self.app.pop_screen()
