# ui/widgets/vim_list.py
from textual.widgets import ListView
from ui.keybinds import NAV_BINDINGS

class VimListView(ListView):
    """A ListView that supports Vim navigation keys by default."""
    
    # Load bindings from the config file
    BINDINGS = NAV_BINDINGS
    
    def action_go_top(self):
        """Move cursor to the first item."""
        if self.children:
            self.index = 0
            self.scroll_to_widget(self.children[0])

    def action_go_bottom(self):
        """Move cursor to the last item."""
        if self.children:
            self.index = len(self.children) - 1
            self.scroll_to_widget(self.children[-1])
