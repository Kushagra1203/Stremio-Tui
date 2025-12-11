# ui/screens/player.py
from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Label, LoadingIndicator
from textual.screen import Screen
from textual import work
from rich.text import Text
import re
import subprocess
import tempfile
import os
from pathlib import Path

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
        # Removed Header()
        yield Label(f"Fetching Streams: {self.display_title}", id="screen_title")
        yield LoadingIndicator(id="loading")
        yield ListView(id="stream_list")
        # Removed Footer()

    def on_mount(self):
        self.fetch_streams()

    @work
    async def fetch_streams(self):
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
        
        # Calculate available width
        screen_width = self.app.console.size.width
        if screen_width < 80: screen_width = 80
        available_width = screen_width - 4

        for s in streams:
            if not isinstance(s, dict): continue 

            # --- 1. Provider Tag ---
            raw_provider = s.get('provider') or s.get('name', 'UNK')
            raw_provider = raw_provider.replace('\n', ' ')
            
            if "Torrentio" in raw_provider: provider_tag = "Tor"
            elif "Comet" in raw_provider: provider_tag = "Comet"
            else: provider_tag = raw_provider[:5]

            # --- 2. Extract Stats (Seeds/Size) ---
            full_title = s.get('title', '')
            bh = s.get('behaviorHints', {})
            
            size_str = ""
            seed_str = ""

            if bh.get('videoSize'):
                size_str = format_size(bh.get('videoSize'))
            
            if s.get('seeds') is not None:
                seed_str = str(s['seeds'])

            # Regex Fallbacks
            if not size_str:
                size_match = re.search(r'(?:💾|📦|Size)\s?([\d\.]+\s?[KMGT]B)', full_title, re.IGNORECASE)
                if size_match: 
                    size_str = size_match.group(1)
                else:
                    loose_match = re.search(r'(\d+(?:\.\d+)?\s?[KMGT]B)', full_title)
                    if loose_match: size_str = loose_match.group(1)

            if not seed_str:
                seed_match = re.search(r'(?:👤|👥|S:)\s?(\d+)', full_title)
                if seed_match: seed_str = seed_match.group(1)

            # --- 3. Clean Filename ---
            if '\n' in full_title: 
                filename = full_title.split('\n')[0]
            else: 
                filename = full_title
            
            if not filename: filename = bh.get('filename')
            if not filename: filename = "Unknown Release"

            # --- 4. Resolution Tag ---
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

            # --- 5. Build Stats String ---
            stats_parts = []
            if size_str: stats_parts.append(f"💾 {size_str}")
            if seed_str: stats_parts.append(f"👤 {seed_str}")
            stats_display = "  ".join(stats_parts)

            # --- 6. Smart Truncation ---
            reserved_len = len(provider_tag) + 3 
            if res_tag: reserved_len += len(res_tag) + 3
            if stats_display: reserved_len += len(stats_display) + 3
            
            allowed_title_len = available_width - reserved_len
            if allowed_title_len < 10: allowed_title_len = 10
            
            display_filename = filename.strip()
            if len(display_filename) > allowed_title_len:
                display_filename = display_filename[:allowed_title_len-1] + "…"

            # --- 7. Construct Rich Text ---
            final_text = Text()
            final_text.append(f"[{provider_tag}] ", style="bold blue")
            if res_tag: final_text.append(f"[{res_tag}] ", style=res_color)
            
            final_text.append(display_filename)
            
            if stats_display:
                final_text.append(" | ", style="dim")
                final_text.append(stats_display, style="cyan")

            link = s.get('url') or s.get('infoHash')
            if not link: continue
            if not link.startswith("magnet") and not link.startswith("http"):
                link = f"magnet:?xt=urn:btih:{link}"
            
            list_view.append(StreamItem(final_text, link))

    def on_list_view_selected(self, message: ListView.Selected):
        item = message.item
        link = item.link 
        
        # Save to History
        self.app.manager.add_to_history({
            "imdb_id": self.imdb_id,
            "title": self.media_title,
            "type": self.type_,
            "year": "",
            "season": self.season,
            "episode": self.episode,
            "stream_link": link 
        })
        
        self.app.notify(f"Launching MPV (Disk Cache Enabled)...")
        
        with self.app.suspend():
            subprocess.run(["clear"]) 
            
            # --- FIX STARTS HERE ---
            # 1. Define a persistent cache folder in your HOME directory (Physical Disk)
            cache_root = Path.home() / ".cache" / "stremio-tui"
            cache_root.mkdir(parents=True, exist_ok=True)

            # 2. Create a modified environment for the subprocess
            # This forces WebTorrent (and underlying Node process) to use the physical disk for temp files
            my_env = os.environ.copy()
            my_env["TMPDIR"] = str(cache_root)
            my_env["TEMP"] = str(cache_root)
            my_env["TMP"] = str(cache_root)

            # 3. Create the temporary directory INSIDE the cache root
            # dir=cache_root ensures it's created on the physical disk, not /tmp
            with tempfile.TemporaryDirectory(prefix="stremio_", dir=cache_root) as tmp_dir:
                print(f"Caching stream to: {tmp_dir}")
                print("Folder will be deleted when player closes.")
                
                cmd = [
                    "webtorrent", link,
                    "--out", tmp_dir, 
                    "--mpv", 
                    "--player-args=--save-position-on-quit" 
                ]
                
                # 4. Run with the custom environment
                subprocess.run(cmd, env=my_env)
            # --- FIX ENDS HERE ---
