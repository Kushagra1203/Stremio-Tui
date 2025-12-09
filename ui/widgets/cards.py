# ui/widgets/cards.py
from textual.app import ComposeResult
from textual.widgets import Label, ListItem
from rich.text import Text

class ResultItem(ListItem):
    """Search Result Item"""
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
