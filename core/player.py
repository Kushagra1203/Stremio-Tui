# core/player.py
"""Launching playback.

This is the only place in the app that shells out to an external player, so it
is also the only place that has to care whether those binaries exist. Both the
stream picker and the history/resume path go through :func:`play_stream`; before
that they each built their own `webtorrent` command line and only one of them
used the disk cache.

`webtorrent` and `mpv` are not Python packages and cannot be installed from
requirements.txt. They are external executables, so a missing one is an ordinary
setup problem, not a crash: we check `PATH` first and raise
:class:`PlayerUnavailable` with something the user can act on.
"""

import os
import shutil
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

from config import TRACKERS

CACHE_ROOT = Path.home() / ".cache" / "stremio-tui"

PLAYER_ARGS = "--save-position-on-quit"

_INSTALL_HINT = {
    "webtorrent": "npm install -g webtorrent-cli",
    "mpv": "install mpv from your package manager (dnf install mpv)",
}


class PlayerUnavailable(RuntimeError):
    """An external playback dependency is missing or unusable.

    Carries a one-line, user-facing message; browsing still works without it.
    """


def check_player_dependencies():
    """Raise :class:`PlayerUnavailable` if webtorrent or mpv is not on PATH."""
    for binary in ("webtorrent", "mpv"):
        if shutil.which(binary) is None:
            raise PlayerUnavailable(
                f"{binary} not found on PATH - {_INSTALL_HINT[binary]}"
            )


def build_magnet(name, info_hash, trackers=None, sources=()):
    """Build a magnet URI that a standalone client can actually find peers for.

    A bare ``magnet:?xt=urn:btih:<hash>`` has no tracker list, so a client
    that is not part of the Stremio ecosystem has nothing to announce to and
    reports "0 peers" indefinitely. Stremio's own player hides this because
    its torrent engine injects trackers internally.

    ``sources`` is the addon's optional tracker list (``["tracker:udp://..."]``
    entries); anything it provides is kept alongside our defaults.
    """
    trackers = list(TRACKERS if trackers is None else trackers)
    for source in sources or ():
        if str(source).startswith("tracker:"):
            url = str(source).split(":", 1)[1]
            if url not in trackers:
                trackers.append(url)

    # The display name is cosmetic, but some trackers reject a magnet without
    # one, and a stray newline in a title would be percent-encoded noise.
    lines = str(name or "").strip().splitlines()
    clean_name = lines[0][:120].strip() if lines else ""

    # Built by hand rather than with urlencode: webtorrent 3.x rejects a
    # magnet whose `xt` is percent-encoded ("Invalid torrent identifier"), so
    # the colons in `urn:btih:` have to stay literal. The tracker URLs and the
    # display name are still percent-encoded, because they contain characters
    # that would otherwise break the query string.
    parts = [f"xt=urn:btih:{info_hash}"]
    if clean_name:
        parts.append("dn=" + urllib.parse.quote(clean_name, safe=""))
    parts.extend("tr=" + urllib.parse.quote(tracker, safe="") for tracker in trackers)

    return "magnet:?" + "&".join(parts)


def resolve_stream_link(stream, trackers=None):
    """Return something playable for a Stremio stream object.

    Addons vary: some hand back a ready ``url`` (an http .torrent link or a
    full magnet), some only an ``infoHash`` plus a ``fileIdx``. The latter is
    the common case and needs trackers added.
    """
    url = stream.get("url")
    if url:
        return url

    info_hash = stream.get("infoHash")
    if not info_hash:
        raise PlayerUnavailable(
            "stream has neither a url nor an infoHash - cannot play it"
        )

    return build_magnet(
        stream.get("title") or stream.get("name") or "",
        info_hash,
        trackers=trackers,
        sources=stream.get("sources") or (),
    )


def build_command(link, out_dir, select=None):
    """The webtorrent invocation. Split out so it can be asserted in a test."""
    cmd = [
        "webtorrent", link,
        "--out", str(out_dir),
        "--mpv",
        f"--player-args={PLAYER_ARGS}",
    ]
    if select is not None:
        # Torrentio ships `fileIdx`, the index of the wanted file inside a
        # multi-file season pack. Without it webtorrent either lists every
        # file or grabs the whole pack.
        cmd.extend(["--select", str(select)])
    return cmd


def play_stream(link, select=None, cache_root=CACHE_ROOT):
    """Block until the player exits. Call this inside ``app.suspend()``.

    Downloads are written under ``cache_root`` rather than the default temp
    directory, so a multi-gigabyte stream does not fill a tmpfs or get wiped
    mid-playback. The temporary directory is removed when the player exits.

    Returns the player's exit code.
    """
    check_player_dependencies()

    cache_root = Path(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    for var in ("TMPDIR", "TEMP", "TMP"):
        env[var] = str(cache_root)

    subprocess.run(["clear"])
    with tempfile.TemporaryDirectory(prefix="stremio_", dir=cache_root) as tmp_dir:
        print(f"Caching stream to: {tmp_dir}")
        print("Folder will be deleted when the player closes.")
        return subprocess.run(
            build_command(link, tmp_dir, select=select), env=env
        ).returncode
