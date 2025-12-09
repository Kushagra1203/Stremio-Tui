# ui/widgets/sidebar.py
from textual.app import ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Label, Static
from textual_image.widget import Image

# Import from our new core utils
from core.utils import fmt_rating, format_date

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
        min-width: 40;
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
