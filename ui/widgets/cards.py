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
        self.stream_link = stream_link

    def compose(self) -> ComposeResult:
        # Determine Icon and clean Type Label
        if self.stream_link:
            icon = "⏯ "
            type_str = "RESUME"
        else:
            icon = ":: "
            # Clean up the type string
            raw_type = str(self.type_).lower()
            if raw_type in ["feature", "movie"]:
                type_str = "MOVIE"
            elif raw_type in ["tv series", "series"]:
                type_str = "SERIES"
            else:
                type_str = raw_type.upper() if raw_type else "UNKNOWN"

        # Build the Main Text (Left Side)
        t = Text(icon, style="dim")
        t.append(f"{self.title_text} ", style="bold white")
        
        if self.year:
            t.append(f"({self.year})", style="dim white")
            
        yield Label(t)
        
        # Build the Badge (Right Side)
        yield Label(f"[{type_str}]", classes="result_type")
