import sys
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box

def render_sidebar(data_file, item_id):
    console = Console()
    
    # 1. Load Data
    try:
        with open(data_file, 'r') as f:
            data_map = json.load(f)
        item = data_map.get(str(item_id))
    except:
        item = None

    if not item:
        console.print("[red]No Data[/]")
        return

    # 2. Extract Info
    title = item.get('title', 'Unknown')
    year = item.get('year', '')
    rating = item.get('rating', 'N/A')
    plot = item.get('overview', item.get('description', 'No description.'))
    poster = item.get('poster')

    # 3. Render Image (Optional - requires 'chafa' installed)
    # We try to render the image directly into the terminal if available
    if poster and os.path.exists(poster):
        # This is where we show the "Photo"
        # We assume the main app downloaded the poster to a temp path
        pass 

    # 4. Build Text Layout
    # Header
    header = Text(f"{title}\n", style="bold #d7005f justify=center")
    if year:
        header.append(f"({year})", style="dim white")

    # Stats
    stats = Text()
    stats.append(f"\n⭐ Score: {rating}\n", style="gold1")
    
    # Plot
    body = Text(f"\n{plot}", style="#cccccc")

    # Combine
    content = Text.assemble(header, "\n", stats, "\n", body)

    # 5. Print as a Panel (The Sidebar Look)
    panel = Panel(
        content,
        border_style="#d7005f",
        title="Details",
        title_align="left",
        box=box.ROUNDED,
        expand=True,
        height=None # Fill available height
    )
    
    console.print(panel)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    # args: script.py <cache_file_path> <item_id>
    render_sidebar(sys.argv[1], sys.argv[2])
