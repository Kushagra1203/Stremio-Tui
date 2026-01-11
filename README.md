# Stremio-Tui 

A lightweight, keyboard-first terminal user interface (TUI) for browsing and interacting with Stremio content. Stremio-Tui aims to provide a fast, distraction-free way to search, browse, and play content from your Stremio account directly from the terminal.

## Features

- Keyboard-driven TUI for browsing movies, TV shows, and addons
- Search and filter content quickly from the terminal
- View metadata, posters and episode lists inline
- Launch content in external players or open via Stremio
- Configurable: API endpoints, preferred player, caching options
- Lightweight and fast — designed for power users and remote servers

## Table of contents

- [Install](#install)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)

## Install

Requirements:
- Python 3.10+
- Git (for installing from source)
- Optional: a terminal that supports true color for best visuals

Recommended: create a virtual environment.

From source
```bash
git clone https://github.com/Kushagra1203/Stremio-Tui.git
cd Stremio-Tui
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

run the module directly:
```bash
python3 main.py
```

Common actions:
- Arrow keys / hjkl to navigate
- Enter to select an item
- / to search
- q to quit
(Adjust keys above to match the actual keybindings implemented in the project.)

Examples:
- Search for a movie:
  1. Start the application: `stremio-tui`
  2. Press `/`
  3. Type the movie name and press Enter
- Play the selected stream:
  - Press `p` (or the configured play key) to open the stream in your default player

## Configuration

Configuration can be provided via a config file or environment variables. Typical options include:

- `STREMIO_API_URL` — Stremio API URL (if using a custom endpoint)
- `STREMIO_TOKEN` — Authentication token (if required)
- `STREMIO_TUI_PLAYER` — Command to launch an external player (e.g., `mpv {url}`)
- `STREMIO_TUI_CACHE_DIR` — Path to cache metadata and images

Example config file (`~/.config/stremio-tui/config.yaml`):
```yaml
player: "mpv {url}"
api_url: "https://api.stremio.com"
cache_dir: "~/.cache/stremio-tui"
token: ""
```

Adjust the keys and format to match your project's actual configuration loader (YAML, JSON, or dotenv).

## Development

To run the project locally for development:
1. Create and activate a virtualenv.
2. Install dev dependencies:
```bash
pip install -r requirements-dev.txt
```
3. Run the app using the module:
```bash
python -m stremio_tui
```

Testing
```bash
pytest
```

Linting and formatting
```bash
ruff check .
black .
```

## Roadmap / Ideas

- Add plugin/addon browser and auto-install
- Offline caching for metadata and images
- Improved keyboard customization and keybinding profiles
- Optional theme support (dark/light)

---
