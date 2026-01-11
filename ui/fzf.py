import os
import shutil
import subprocess
import json
import tempfile
from pathlib import Path

class Fzf:
    def __init__(self):
        self.executable = shutil.which("fzf")
        if not self.executable:
            raise RuntimeError("Please install 'fzf' (sudo dnf install fzf)")
        
        # Define Cache for Previews
        self.cache_dir = Path.home() / ".cache" / "stremio-tui" / "fzf_ctx"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.current_data_file = self.cache_dir / "current_view.json"

    def run(self, items, prompt="Select"):
        """
        items: List of dicts. MUST have 'id' and 'display_text'.
               Optional: 'poster', 'overview' for the sidebar.
        """
        # 1. Save state for the Preview Script
        data_map = {str(i['id']): i for i in items}
        with open(self.current_data_file, 'w') as f:
            json.dump(data_map, f)

        # 2. Build Input List (ID | Display)
        # We use ||| as a separator
        fzf_input = []
        for i in items:
            # We pass the ID so preview.py knows what to look up
            line = f"{i['id']}|||{i['display_text']}"
            fzf_input.append(line)
        
        input_str = "\n".join(fzf_input)

        # 3. Calculate Preview Command
        # This calls our python script to generate the sidebar on the fly
        preview_cmd = f"python3 ui/preview.py {self.current_data_file} {{1}}"

        # 4. FZF Options (The Layout)
        # --preview-window=left:30% -> Sidebar on Left (30% width)
        cmd = [
            self.executable,
            "--prompt", f"{prompt} > ",
            "--delimiter", "\|\|\|",
            "--with-nth", "2..",     # Hide the ID from the list
            "--preview", preview_cmd,
            "--preview-window", "left:30%:rounded:wrap", # <--- THE SIDEBAR LAYOUT
            "--layout", "reverse",   # Top-down list
            "--border", "rounded",
            "--margin", "1",
            "--ansi",                # Allow colors
            "--cycle"
        ]

        # 5. Run
        result = subprocess.run(
            cmd,
            input=input_str,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            return None

        # 6. Parse Result (Get the ID back)
        # Output: "tt12345|||Stranger Things..."
        try:
            selected_line = result.stdout.strip()
            selected_id = selected_line.split("|||")[0]
            return data_map.get(selected_id)
        except:
            return None

    def ask(self, question):
        # Quick input method
        try:
            print(f"\n{question}: ", end="")
            return input()
        except KeyboardInterrupt:
            return None
