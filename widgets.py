from textual.app import ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Label, Static
from textual_image.widget import Image
import re
from core import format_date

# --- HELPER FUNCTIONS ---
def fmt_rating(val):
    if val is None or val == "": return "N/A"
    try:
        f_val = float(val)
        if f_val == 0: return "N/A"
        return f"⭐ {f_val:.1f}"
    except:
        return "N/A"

def fmt_runtime(val):
    if not val or val == "N/A": return "N/A"
    if isinstance(val, (int, float)):
        try:
            mins = int(val)
            if mins > 60: return f"{mins // 60}h {mins % 60}m"
            return f"{mins}m"
        except: pass
    
    s_val = str(val).lower().strip()
    if s_val.isdigit():
        mins = int(s_val)
        if mins > 60: return f"{mins // 60}h {mins % 60}m"
        return f"{mins}m"

    match = re.search(r'(?:(\d+)h)?\s*(\d+)', s_val)
    if match:
        h, m = match.groups()
        h = int(h) if h else 0
        m = int(m) if m else 0
        if h > 0: return f"{h}h {m}m"
        return f"{m}m"
    return s_val

# --- UI COMPONENTS ---

class MetaRow(Static):
    """A single row of metadata (Label + Value)."""
    
    DEFAULT_CSS = """
    MetaRow {
        layout: horizontal;
        height: auto;
        margin-bottom: 0;
        padding: 0;
    }
    
    .meta_label {
        width: 12;
        color: #d7005f; 
        text-style: bold;
    }
    
    .meta_value {
        width: 1fr;
        color: #eeeeee;
    }
    """

    def __init__(self, label, value, **kwargs):
        super().__init__(**kwargs)
        self.label_text = label
        self.value_text = value

    def compose(self) -> ComposeResult:
        yield Label(self.label_text, classes="meta_label")
        yield Label(str(self.value_text), classes="meta_value")

    def update_data(self, label, value):
        self.query_one(".meta_label").update(label)
        self.query_one(".meta_value").update(str(value))

class SeriesSidebar(Vertical):
    """
    The Left Sidebar Component.
    """
    
    DEFAULT_CSS = """
    SeriesSidebar {
        width: 35%;
        min-width: 40; /* FIX 1: Ensure it's never too narrow for the image */
        height: 100%; 
        border-right: solid #333; 
        padding: 1 2; 
        background: #111;
        overflow-y: auto; 
        scrollbar-size: 0 0; 
    }
    
    #poster_container { 
        height: auto;
        align: center middle; 
        margin-bottom: 1;
    }
    
    /* FIX 2: Removed max-height so poster isn't cut vertically */
    #poster_image { 
        width: 30; 
        height: auto; 
    }

    #info_title { 
        text-align: center; 
        color: #fff; 
        text-style: bold; 
        background: #d7005f; 
        padding: 1; 
        width: 100%; 
        margin-bottom: 1; 
    }

    #meta_table { 
        height: auto; 
        margin-bottom: 1; 
    }

    #ep_desc { 
        color: #888; 
        height: auto; 
        min-height: 5;
        border-top: solid #333; 
        padding-top: 1; 
        margin-top: 1; 
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Loading...", id="info_title")
        
        with Container(id="poster_container"):
            yield Image(id="poster_image")
        
        with Vertical(id="meta_table"):
            yield MetaRow("Score", "-", id="row_1")
            yield MetaRow("Status", "-", id="row_2")
            yield MetaRow("Year", "-", id="row_3")
            yield MetaRow("Duration", "-", id="row_4")
            yield MetaRow("Genres", "-", id="row_5")
        
        yield Static("", id="ep_desc")

    def update_image(self, pil_image):
        if pil_image:
            try:
                self.query_one("#poster_image", Image).image = pil_image
            except: 
                pass

    def show_series_data(self, meta, runtime_str):
        name = meta.get('name', 'Unknown')
        desc = meta.get('description', 'No description.')
        year = meta.get('year', 'N/A')
        status = meta.get('status', 'N/A')
        
        if str(year) in str(status) and len(status) < 10: 
            status = "Released"

        rating = fmt_rating(meta.get('rating'))
        genres = ", ".join(meta.get('genres', [])[:3])

        self.query_one("#info_title").update(name)
        self.query_one("#ep_desc").update(desc)

        self.query_one("#row_1", MetaRow).update_data("Score", rating)
        
        r2 = self.query_one("#row_2", MetaRow)
        r2.display = True
        r2.update_data("Status", status)

        self.query_one("#row_3", MetaRow).update_data("Year", year)
        self.query_one("#row_4", MetaRow).update_data("Runtime", runtime_str)
        
        r5 = self.query_one("#row_5", MetaRow)
        r5.display = True
        r5.update_data("Genres", genres)

    def show_episode_data(self, ep, series_runtime_str):
        self.query_one("#info_title").update(ep.get('name', 'Unknown'))
        self.query_one("#ep_desc").update(ep.get('overview') or "No synopsis.")

        released = format_date(ep.get('released'))
        rating = fmt_rating(ep.get('rating'))

        self.query_one("#row_1", MetaRow).update_data("Score", rating)
        
        r2 = self.query_one("#row_2", MetaRow)
        r2.display = True
        r2.update_data("Aired", released)

        self.query_one("#row_3", MetaRow).update_data("Runtime", series_runtime_str)
        self.query_one("#row_4", MetaRow).update_data("Format", "TV Episode")
        
        self.query_one("#row_5", MetaRow).display = False
