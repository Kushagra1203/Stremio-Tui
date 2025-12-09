# ui/screens/player.py
from textual.app import ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, LoadingIndicator
from textual.screen import Screen
from textual import work
from rich.text import Text
import re
import subprocess

# Import helpers from core
from core.utils import format_size

class StreamItem(ListItem):
    def __init__(self, display_renderable, link):
        super().__init__()
        self.display_renderable = display_renderable
        self.link = link

    def compose(self) -> ComposeResult:
        yield Label(self.display_renderable)

class StreamSelectScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    
    CSS = """
    StreamSelectScreen {
        layer: above; 
        layout: vertical;
    }
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
        # NOTE: We now access the manager via self.app.manager
        manager = self.app.manager
        
        streams = await manager.get_streams(self.type_, self.stremio_id)
        
        list_view = self.query_one("#stream_list")
        loading = self.query_one("#loading")
        title_label = self.query_one("#screen_title")
        
        loading.display = False
        
        if not streams:
            title_label.update(f"No streams found for {self.display_title}")
            return

        title_label.update(f"Select Stream: {self.display_title} ({len(streams)} found)")
        
        available_width = self.app.console.size.width - 6

        for s in streams:
            if not isinstance(s, dict): continue 

            # 1. Provider Tag
            raw_provider = s.get('provider') or s.get('name', 'UNK')
            raw_provider = raw_provider.replace('\n', ' ')
            
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

            # 4. Stats
            info_parts = []
            if bh.get('videoSize'):
                info_parts.append(f"📦 {format_size(bh.get('videoSize'))}")

            if s.get('seeds') is not None:
                 info_parts.append(f"👥 {s['seeds']}")

            stats_str = "  ".join(info_parts)

            # 5. Build Text
            final_text = Text()
            final_text.append(f"[{provider_tag}] ", style="bold blue")
            if res_tag: final_text.append(f"[{res_tag}] ", style=res_color)
            final_text.append(filename[:50]) # Simple truncation
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
        self.app.notify(f"Launching MPV...")
        with self.app.suspend():
            subprocess.run(["clear"]) 
            subprocess.run(["webtorrent", link, "--mpv"])
