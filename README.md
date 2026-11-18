# Stremio TUI

A keyboard-driven terminal client for browsing Stremio catalogues: search, inspect
metadata and episode lists, list available streams, and hand playback to an external
player.

It exists because I live in a terminal and wanted a fast, distraction-free way to
answer "what do I watch next" without opening a browser.

```
 search  ──▶  IMDb suggestion API  ──▶  results list
                                          │
                                          ▼
                             metadata merge (Cinemeta + TVMaze/TMDB/AniList/OMDb)
                                          │
                                          ▼
                             Stremio stream addons (Torrentio, Comet)
                                          │
                                          ▼
                                  webtorrent ──▶ mpv
```

## Requirements

- Python 3.10+
- `webtorrent` CLI and `mpv` on `PATH` (playback only — browsing works without them)
- Optional: `OMDB_API_KEY` environment variable for season ratings

Python dependencies are pinned in `requirements.txt`:

| Package | Why |
|---|---|
| `textual`, `rich` | TUI framework and text rendering |
| `textual-image` | renders poster images inside the terminal |
| `httpx` | async HTTP client shared across all API calls |
| `Pillow` | decodes downloaded posters |

## Install and run

```bash
git clone https://github.com/Kushagra1203/Stremio-Tui.git
cd Stremio-Tui

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 main.py
```

## Keys

| Key | Action |
|---|---|
| `i` / `/` | focus the search box |
| `Esc` | back to the list (normal mode) |
| `j` / `k` | move down / up |
| `g` / `G` | jump to top / bottom |
| `Enter` | open the selected item |
| `Ctrl+Q` | quit |

## Layout

```
main.py              entry point
config.py            API endpoints, headers, stream addons
api/                 one mixin per provider, composed into StremioClient
  base.py            shared httpx.AsyncClient (15 s timeout, pooled connections)
  search.py          IMDb suggestion endpoint
  cinemeta.py        catalogue + authoritative season/episode structure
  tvmaze.py          rich episode metadata, HTML-stripped
  tmdb.py            fallback metadata source
  anilist.py         season data for anime
  omdb.py            per-season ratings
  streams.py         queries every addon in parallel, merges the results
core/
  manager.py         orchestration + the metadata merge
  cache.py           bounded LRU poster cache
  history.py         JSON-backed "continue watching"
  utils.py           formatting helpers
ui/                  Textual app, screens, widgets, keybindings
tests/               unit tests for the merge rules and the cache
```

## Design notes

**Which source wins.** Cinemeta has the correct season and episode structure but thin
per-episode text. TVMaze and TMDB have good summaries, thumbnails and names, but their
season lists drift — especially for long-running anime. So Cinemeta decides *which*
episodes exist and the rich source decides *what they say*. They are joined on
`(season, episode)`; anything unmatched keeps its Cinemeta values. That merge lives in
`merge_series_metadata()`, a pure function, so the rules are testable without mocking
HTTP.

**Anime routing.** A show is routed to AniList when its country is Japan or its genres
contain "anime". This is a heuristic, not a classifier. False positives are cheap: if
AniList returns nothing the caller falls back to TVMaze. It exists because AniList
carries season-level data that TVMaze does not, and Japanese shows are where the two
sources disagree most.

**Why the cache is bounded.** Posters are the largest objects the UI holds, and an
unbounded dict was the obvious first version. It is now an LRU with a 64-entry cap, so
scrolling a long list cannot grow memory without limit. It is memory-only: posters are
best-effort decoration, and a cold start simply re-downloads them, so a disk tier would
add an invalidation problem for no real gain at this size.

**Why prefetch instead of lazy load.** Metadata is what makes the list usable, so the
top 20 results are resolved in parallel with a single `asyncio.gather` before the list
renders. Posters are queued afterwards — they are the slowest part and the UI reads
fine without them for a few hundred milliseconds.

**Blocking work in a TUI.** Network calls are awaited inside Textual `@work` workers so
the event loop keeps rendering. Nothing in the UI thread blocks on I/O.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

Covers the metadata merge (structure precedence, field injection, missing sources,
non-mutation) and the poster cache (LRU eviction, cache hits, failed downloads). The
Textual layer is not covered — it is exercised by hand.

## Known limitations

- Stream addons are hardcoded in `config.py`; there is no addon manager.
- No authentication flows — this browses public catalogue and stream endpoints.
- Provider priority is fixed (TVMaze → TMDB → TVMaze-by-name). A scoring approach
  across sources would be better than first-match-wins.
- Playback assumes `webtorrent` and `mpv` are installed and shell-configured.
- `history.json` is written to the working directory rather than a config path.

## Disclaimer

Personal project, not affiliated with Stremio. It is a client: it reads public
catalogue metadata and lists streams from third-party addons. Whether the content those
addons serve is licensed is outside this project's control and is the user's
responsibility.
