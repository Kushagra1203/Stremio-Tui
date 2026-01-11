# ui/selector.py
import os
import shutil
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

class FzfSelector:
    def __init__(self):
        self.executable = shutil.which("fzf")
        if not self.executable:
            raise RuntimeError("Please install 'fzf' (sudo dnf install fzf)")

        # --- VIU THEME CONFIGURATION ---
        # This sets the colors to Match the Pink/Dark Theme
        # fg/bg = Text/Background
        # hl = Highlighted Text
        # pointer = The arrow selection
        os.environ["FZF_DEFAULT_OPTS"] = (
            "--height=100% "
            "--layout=reverse "
            "--border=rounded "
            "--margin=1 "
            "--padding=1 "
            "--color=bg+:#151515,bg:#000000,spinner:#d7005f,hl:#d7005f "
            "--color=fg:#eeeeee,header:#d7005f,info:#5fafd7,pointer:#d7005f "
            "--color=marker:#d7005f,fg+:#ffffff,prompt:#d7005f,hl+:#d7005f "
            "--prompt='🔎 ' "
            "--pointer='▶' "
            "--marker='✓' "
        )
        self.console = Console()

    def get_selection(self, items, prompt="Select", preview_func=None):
        """
        items: List of dictionaries. MUST have 'display' key. 
               Can optionaly have 'id' or 'preview_text'.
        """
        # 1. Prepare input for FZF
        # Format: "INDEX | DISPLAY_TEXT"
        # We use a weird delimiter "|||" to avoid conflicts with movie titles
        fzf_input = []
        for idx, item in enumerate(items):
            clean_display = item['display'].replace("\n", " ")
            fzf_input.append(f"{idx}|||{clean_display}")
        
        input_str = "\n".join(fzf_input)

        # 2. Build Command
        # --delimiter="|||" : Split by our weird delimiter
        # --with-nth=2      : Only show the 2nd part (The Display Text)
        # --nth=2           : Only search the 2nd part
        commands = [
            self.executable,
            "--prompt", f"{prompt} > ",
            "--delimiter", "\|\|\|", 
            "--with-nth", "2",
            "--nth", "2", 
            "--ansi",
            "--cycle"
        ]

        # 3. Preview Handling (Advanced)
        # Since we can't easily run python functions inside FZF's preview shell,
        # we will pass a generic text preview if available.
        # Ideally, this requires a separate script, but for now we use echo.
        # commands.extend(["--preview", "echo {2}"]) 

        result = subprocess.run(
            commands,
            input=input_str,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

        if result.returncode != 0:
            return None

        # 4. Parse Result
        # Output will be: "5|||Stranger Things..."
        try:
            output = result.stdout.strip()
            index_str = output.split("|||")[0]
            index = int(index_str)
            return items[index] # Return the original object
        except:
            return None

    def ask(self, title):
        """
        A pretty input box using Rich, so it doesn't look like raw terminal.
        """
        self.console.clear()
        self.console.print("\n" * 5) # Push down a bit
        
        text = Align.center(
            f"[bold #d7005f]Enter {title}[/]\n[dim]Press Enter to confirm[/]", 
            vertical="middle"
        )
        self.console.print(Panel(text, border_style="#d7005f", title="Search", width=50, padding=(1, 2)), justify="center")
        
        self.console.print("[bold #d7005f] > [/]", end="")
        return input()
