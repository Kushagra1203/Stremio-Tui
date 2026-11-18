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
from pathlib import Path

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


def build_command(link, out_dir):
    """The webtorrent invocation. Split out so it can be asserted in a test."""
    return [
        "webtorrent", link,
        "--out", str(out_dir),
        "--mpv",
        f"--player-args={PLAYER_ARGS}",
    ]


def play_stream(link, cache_root=CACHE_ROOT):
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
        return subprocess.run(build_command(link, tmp_dir), env=env).returncode
