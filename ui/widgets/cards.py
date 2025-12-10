# ui/widgets/cards.py
from textual.app import ComposeResult
from textual.widgets import Label, ListItem
from rich.text import Text

class ResultItem(ListItem):
    """Search/History Result Item"""
    def __init__(self, title, year, type_, imdb_id, stream_link=None):
        super().__init__()
        self.title_text = title
        self.year = year
        self.type_ = type_ 
        self.imdb_id = imdb_id
        self.stream_link = stream_link # <--- NEW: Store the magnet link

    def compose(self) -> ComposeResult:
        # If it's a History item (has link), color it differently or add icon
        if self.stream_link:
            title_style = "bold magenta" # History style
            icon = "⏯️ "
        else:
            title_style = "bold blue" # Search style
            icon = ""

        t = Text(f"{icon}{self.title_text}", style=title_style)
        if self.year:
            t.append(f" ({self.year})", style="dim")
            
        yield Label(t)
        yield Label(f"{self.type_}", classes="result_type")
