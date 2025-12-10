# ui/keybinds.py
from textual.binding import Binding

# --- List Navigation (Vim Style) ---
# Used by VimListView
NAV_BINDINGS = [
    # Basic Nav (j/k)
    Binding("j", "cursor_down", "Down", show=False),
    Binding("k", "cursor_up", "Up", show=False),
    
    # Jump to Top/Bottom (Mapped to our NEW custom actions)
    Binding("g", "go_top", "Top", show=False),
    Binding("G", "go_bottom", "Bottom", show=False),
    
    # Standard Arrows (Fallback)
    Binding("up", "cursor_up", "Up", show=False),
    Binding("down", "cursor_down", "Down", show=False),
    
    # Selection (Explicitly map enter)
    Binding("enter", "select_cursor", "Select", show=False),
]

# --- Global App Bindings ---
# Used by StremioApp
APP_BINDINGS = [
    Binding("ctrl+c", "quit", "Quit", show=False),
    Binding("ctrl+q", "quit", "Quit", show=True),
    
    # Search / Insert Mode
    Binding("i", "focus_search", "Insert Mode", show=True),
    Binding("/", "focus_search", "Search", show=False),
    
    # Escape to leave Input and go back to list
    Binding("escape", "focus_list", "Normal Mode", show=True),
]
