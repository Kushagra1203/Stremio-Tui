from textual.widgets import Static
from rich.text import Text
from rich.align import Align

LOGO_TEXT = """
 ██████  ████████ ██████  ███████ ███    ███ ██  ██████ 
██       ___██___ ██   ██ ██      ████  ████ ██ ██    ██
███████     ██    ██████  █████   ██ ████ ██ ██ ██    ██
     ██     ██    ██   ██ ██      ██  ██  ██ ██ ██    ██
██████      ██    ██   ██ ███████ ██      ██ ██  ██████ 
"""

class AppLogo(Static):
    def render(self):
        # Centered, Pink Logo
        return Align.center(Text(LOGO_TEXT, style="bold #d7005f"))
