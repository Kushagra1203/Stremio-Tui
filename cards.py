# ui/widgets/cards.py
from textual.app import ComposeResult
from textual.widgets import Label, ListItem
from rich.text import Text

class ResultItem(ListItem):
    """Search/History Result Item - Pure CSS Styling"""
    def __init__(self, title, year, type_, imdb_id, stream_link=None):
        super().__init__()
        self.title_text = title
        self.year = year
        self.type_ = type_ 
        self.imdb_id = imdb_id
        self.stream_link = stream_link

    def compose(self) -> ComposeResult:
        # Use simple text. Let CSS handle colors.
        icon = "⏯ " if self.stream_link else ":: "
        
        t = Text(icon)
        t.append(self.title_text) # No style= here!
        if self.year:
            t.append(f"  {self.year}") # No style= here!
            
        yield Label(t)
        yield Label(f"<{self.type_.upper()}>", classes="result_type")
